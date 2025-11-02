import base64
import asyncio
import json
import os
from tempfile import NamedTemporaryFile
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
import httpx


class InterviewConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conversation_history = []
        
    async def connect(self):
        """Handle WebSocket connection"""
        await self.accept()
        
        try:
            await self.send(text_data=json.dumps({
                "type": "connected",
                "message": "WebSocket connected successfully. Ready for interview!"
            }))
            
            # Send initial greeting
            await self.send_initial_greeting()
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": f"Failed to initialize: {str(e)}"
            }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        print(f"WebSocket disconnected with code: {close_code}")
        self.conversation_history = []

    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            
            if data.get("type") == "audio_chunk":
                await self.handle_audio_chunk(data)
            else:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": f"Unknown message type: {data.get('type')}"
                }))
                
        except json.JSONDecodeError as e:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": f"Invalid JSON: {str(e)}"
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": f"Error processing message: {str(e)}"
            }))

    async def handle_audio_chunk(self, data):
        """Process audio chunk from client"""
        try:
            await self.send(text_data=json.dumps({
                "type": "processing", 
                "message": "Processing your audio..."
            }))
            
            base64_audio = data.get("audio")
            if not base64_audio:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": "No audio data received"
                }))
                return
            
            # Decode audio
            audio_bytes = base64.b64decode(base64_audio)
            
            # Transcribe audio using Groq Whisper
            transcript_text = await self.transcribe_audio_groq(audio_bytes)
            
            if not transcript_text or not transcript_text.strip():
                await self.send(text_data=json.dumps({
                    "type": "info",
                    "message": "No speech detected in audio"
                }))
                return
            
            # Send transcription to client
            await self.send(text_data=json.dumps({
                "type": "transcription",
                "text": transcript_text
            }))
            
            # Generate AI response
            await self.send(text_data=json.dumps({"type": "ai_response_start"}))
            
            full_response = await self.generate_ai_response_groq(transcript_text)
            
            await self.send(text_data=json.dumps({
                "type": "ai_response_end",
                "full_text": full_response
            }))
            
        except Exception as e:
            print(f"Error handling audio chunk: {str(e)}")
            import traceback
            traceback.print_exc()
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": f"Error processing audio: {str(e)}"
            }))

    async def transcribe_audio_groq(self, audio_bytes: bytes) -> str:
        """
        Transcribe audio using Groq Whisper API (FREE)
        Get your API key from: https://console.groq.com/keys
        
        Args:
            audio_bytes: Raw audio bytes
            
        Returns:
            Transcribed text
        """
        try:
            # Create temporary file
            with NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp.flush()
                tmp_path = tmp.name
            
            # Transcribe using Groq Whisper API
            async with httpx.AsyncClient(timeout=30.0) as client:
                with open(tmp_path, "rb") as audio_file:
                    files = {
                        "file": ("audio.webm", audio_file, "audio/webm")
                    }
                    data = {
                        "model": "whisper-large-v3-turbo",  # Fast and accurate
                        "temperature": 0.0,
                        "response_format": "json",
                        "language": "en"
                    }
                    headers = {
                        "Authorization": f"Bearer {settings.GROQ_API_KEY}"
                    }
                    
                    response = await client.post(
                        "https://api.groq.com/openai/v1/audio/transcriptions",
                        files=files,
                        data=data,
                        headers=headers
                    )
                    
                    response.raise_for_status()
                    result = response.json()
            
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except:
                pass
            
            return result.get("text", "").strip()
                
        except Exception as e:
            print(f"Transcription error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Failed to transcribe audio: {str(e)}")

    async def generate_ai_response_groq(self, user_input: str) -> str:
        """
        Generate AI response using Groq (FREE)
        
        Args:
            user_input: User's transcribed text
            
        Returns:
            Full AI response text
        """
        try:
            # Add user message to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })
            
            # Prepare messages
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a professional and friendly AI interviewer conducting a mock interview. "
                        "Your role is to:\n"
                        "1. Ask thoughtful, relevant interview questions\n"
                        "2. Listen carefully to the candidate's responses\n"
                        "3. Provide constructive feedback when appropriate\n"
                        "4. Ask follow-up questions to dive deeper\n"
                        "5. Create a realistic interview experience\n"
                        "6. Be encouraging but professional\n\n"
                        "Keep your responses concise (2-3 sentences max) and natural. "
                        "Alternate between asking questions and acknowledging responses."
                    )
                }
            ] + self.conversation_history[-10:]
            
            # Stream response from Groq
            full_response = ""
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.3-70b-versatile",  # Fast and smart
                        "messages": messages,
                        "stream": True,
                        "temperature": 0.7,
                        "max_tokens": 150,
                        "top_p": 1
                    }
                )
                
                response.raise_for_status()
                
                # Process streaming response
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        
                        if data_str.strip() == "[DONE]":
                            break
                            
                        try:
                            data = json.loads(data_str)
                            if data.get("choices") and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                
                                if content:
                                    full_response += content
                                    
                                    # Send chunk to client
                                    await self.send(text_data=json.dumps({
                                        "type": "ai_response_chunk",
                                        "text": content
                                    }))
                        except json.JSONDecodeError:
                            continue
            
            # Add assistant response to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": full_response
            })
            
            return full_response
            
        except Exception as e:
            print(f"AI response generation error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Failed to generate AI response: {str(e)}")

    async def send_initial_greeting(self):
        """Send initial greeting to start the interview"""
        try:
            greeting = (
                "Hello! I'm your AI interviewer today. "
                "Let's begin with a simple question: "
                "Can you tell me a bit about yourself and your background?"
            )
            
            await self.send(text_data=json.dumps({
                "type": "ai_response_end",
                "full_text": greeting
            }))
            
            # Add to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": greeting
            })
            
        except Exception as e:
            print(f"Error sending initial greeting: {str(e)}")
            import traceback
            traceback.print_exc()