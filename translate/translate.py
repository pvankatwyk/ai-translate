import openai
import pyaudio
import wave
import tempfile
from pathlib import Path
import pydub
from pydub import AudioSegment
from threading import Thread
import subprocess
import queue
import time
import threading
import numpy as np
import os

# Initialize OpenAI client
api_key = os.environ["OPENAI_API_KEY"]
pydub.AudioSegment.ffmpeg = r"C:\ffmpeg\bin"
AudioSegment.converter = r"C:\ffmpeg\bin\ffmpeg.exe"
client = openai.OpenAI(api_key=api_key)

# Queue to hold audio chunks for processing
audio_queue = queue.Queue()

# Flag to control thread execution
running = True

# Additional queue to handle playback tasks
playback_queue = queue.Queue()

def listen_audio():
    global running
    silence_threshold = 100  # Adjust this threshold based on environment
    chunk_duration = 120  # Number of frames per chunk
    audio = pyaudio.PyAudio()
    
    while running:
        try:
            stream = audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
            print("Listening...")
            
            while running:
                audio_data = []
                for _ in range(chunk_duration):  # Collect ~1 second of audio
                    data = stream.read(1024)
                    audio_data.append(data)
                
                # Convert audio data to numpy array for amplitude analysis
                audio_array = np.frombuffer(b''.join(audio_data), dtype=np.int16)
                amplitude = np.mean(np.abs(audio_array))

                # Only add non-silent chunks to the queue
                if amplitude > silence_threshold:
                    print(f"Queue size before adding: {audio_queue.qsize()}")
                    audio_queue.put(audio_data)
                    print(f"Queue size after adding: {audio_queue.qsize()}")
                else:
                    pass

        except Exception as e:
            print(f"Stream error: {e}")
            time.sleep(1)
            continue

        finally:
            if stream.is_active():
                stream.stop_stream()
            stream.close()
    audio.terminate()

def transcribe_translate_speak():
    global running
    unwanted_phrases = {"thanks for watching", "like comment and subscribe", "subscribe", "follow us"}  # Add other common YouTube/video phrases as needed
    
    while running:
        temp_audio_file_path = None
        try:
            audio_data = audio_queue.get(timeout=5)

            # Save audio_data to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
                temp_audio_file_path = Path(temp_audio_file.name)
                wf = wave.open(str(temp_audio_file_path), 'wb')
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(b''.join(audio_data))
                wf.close()
                
            # Transcribe
            try:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=temp_audio_file_path, 
                    response_format="text"
                )
                
                # Check for unwanted phrases
                if any(phrase in transcription.lower() for phrase in unwanted_phrases):
                    print(f"Ignored transcription due to unwanted content: {transcription}")
                    continue  # Skip to the next transcription if unwanted content is detected
                
                print(f"Transcription: {transcription}")
                
                # Save transcription to file
                with open("transcription_log.txt", "a") as f:
                    f.write(transcription + "\n")  # Add new line for readability

            except Exception as e:
                print(f"Transcription error: {e}")
                continue

            # Translate
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a translator for a live event for the Church of Jesus Christ of Latter Day Saints. Speakers will be talking about Jesus, the Book of Mormon, and stories and doctrines specific to the Church of Jesus Christ of Latter Day Saints. Any translation should be in compliance with teachings and doctrines from the Church of Jesus Christ of Latter Day saints. Accordingly, translate the following text to Spanish."},
                        {"role": "user", "content": transcription}
                    ]
                )
                translation = response.choices[0].message.content
                print(f"Translation: {translation}")
                
                # Save translation to file
                with open("translation_log.txt", "a") as f:
                    f.write(translation + "\n")  # Add new line for readability

            except Exception as e:
                print(f"Translation error: {e}")
                continue

            # Text-to-speech and enqueue playback
            speech_file_path = temp_audio_file_path.with_suffix(".wav")
            try:
                with client.audio.speech.with_streaming_response.create(
                    model="tts-1",
                    voice="alloy",
                    input=translation,
                ) as response:
                    response.stream_to_file(speech_file_path)
                
                # Add the audio file path to playback queue
                playback_queue.put(speech_file_path)

            except Exception as e:
                print(f"TTS error: {e}")
                continue

            # Signal that the queue item has been processed
            audio_queue.task_done()

        except queue.Empty:
            continue
        except Exception as e:
            print(f"Processing error: {e}")



# `handle_playback` remains the same, solely responsible for deleting files after playback


# Separate function to handle playback asynchronously
def handle_playback():
    while running:
        try:
            speech_file_path = playback_queue.get(timeout=5)
            
            # Check if the file is ready and wait briefly if necessary
            for _ in range(10):  # Try up to 10 times (1 second total)
                if os.path.exists(speech_file_path):
                    break
                time.sleep(0.1)  # Wait 100ms before checking again
            
            # Play the file if it exists
            if os.path.exists(speech_file_path):
                ffplay_process = subprocess.Popen(
                    ["ffplay", "-nodisp", "-autoexit", str(speech_file_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                ffplay_process.wait()  # Wait for playback to finish
                os.remove(speech_file_path)  # Delete file after playback completes
                # print(f"Audio file played and deleted: {speech_file_path}")
            else:
                print(f"File {speech_file_path} was not found for playback.")

            playback_queue.task_done()

        except queue.Empty:
            continue
        except Exception as e:
            print(f"Playback error: {e}")

def main():
    global running
    try:
        # Start the listening thread
        listener_thread = threading.Thread(target=listen_audio)
        listener_thread.daemon = True
        listener_thread.start()

        # Start the transcription/translation thread
        processing_thread = threading.Thread(target=transcribe_translate_speak)
        processing_thread.daemon = True
        processing_thread.start()

        # Start the playback thread
        playback_thread = threading.Thread(target=handle_playback)
        playback_thread.daemon = True
        playback_thread.start()

        # Keep the main thread running and check for KeyboardInterrupt
        while running:
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nExiting...")
        running = False  # Signal all threads to stop

        # Ensure all threads complete their tasks
        listener_thread.join()
        processing_thread.join()
        playback_thread.join()
        print("All threads have been stopped.")

if __name__ == "__main__":
    main()

