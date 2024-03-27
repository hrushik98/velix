
import streamlit as st
from openai import OpenAI
from moviepy.editor import concatenate_videoclips, VideoFileClip
import os
import shutil
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
import os
from pdf2image import convert_from_path
from moviepy.editor import ImageSequenceClip, AudioFileClip
import shutil

def app():
    import os
    import streamlit as st
    api_key = st.text_input("Enter your API key",type = "password")
    client = OpenAI(api_key = api_key)
    if os.path.exists("session_folder"):
        shutil.rmtree("session_folder")
        os.mkdir("session_folder")
    else:
        os.mkdir("session_folder")
    system_message = """
    You are a teacher with decades of experience in teaching students of all levels and languages. You are 
    talented and help students to learn and understand the subject matter. You will be given a 
    lesson name, the book name, the age group of the student. 
    You have to seperate the lessons into different sections and give two descriptions of each section.
    Example: Section <number>: <title>
    short description: <short description including the important keywords and names>
    long description: <long description including the important keywords and names>
    <leave a line after each full section>
    Give a minimum of 5 sections and a maximum of 10 sections.
    make sure to use vocabulary and language that is suitable for the age group of the student.
    produce a verbatim script with filler words like uh, um, so etc.., so that it sounds natural.
    """
    st.title("Velix")
    st.markdown("""
                > High quality narration videos in minutes!
                """)

    lesson_name = st.text_input('Enter lesson name', value='Example: Quality')
    book_name = st.text_input('Enter book name', value = "Example: Ncert class 7 English")
    age_group = st.text_input("enter age group", value = "Example: 10-12 years")
    script = st.text_area('Enter script here', height=200)
    special_instructions = st.text_area('enter special instructions (leave blank if none)', height = 100, value = "Example: Please use vocabulary according to the age group")
    speed = st.select_slider('Select Speed', options=[0.75, 1, 1.25, 1.5], value = 1)
    voice = st.selectbox('Select Voice', ("alloy", "echo", "fable", "nova", "onyx", "shimmer"))
    
    if st.button("Let's go"):
        user_message = f"""
        Lesson Name: {lesson_name}
        Book Name: {book_name}
        Age Group: {age_group}
        Special isntructions: {special_instructions}
        script: {script}
        """
        if len(user_message)/4 > 4000:
            st.error("Please keep the script under 16000 characters")
        else:
            user_message = f"""
            Lesson Name: {lesson_name}
            Book Name: {book_name}
            Age Group: {age_group}
            Special isntructions: {special_instructions}
            script: {script}
            """
            st.success("Processing")
            #generate script
            response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
            {"role": "system", "content": f"{system_message}"},
            {"role": "user", "content": f"{user_message[0:16000]}",
            ],
            max_tokens=3000
            )
            full_script=response.choices[0].message.content
            print(full_script)
            sections = full_script.split("\n\n")
            for k in range(0,len(sections)):
                
                slide_title = sections[k].split("\n")[0]
                short_description = sections[k].split("\n")[1][18:]
                long_description = sections[k].split("\n")[2][17:]
                speech_file_path = "session_folder/audio.mp3"
                try:
                    os.remove("session_folder/presentation.pdf")
                except:
                    pass
                try:
                    os.remove("session_folder/presentation.pptx")
                except:
                    pass
                try:
                    os.remove("audio.mp3")
                except:
                    print("failed to remove")

                response = client.audio.speech.create(
                  model="tts-1",
                  voice=voice,
                  input=f"{long_description}",
                  speed=speed
                )
                response.stream_to_file(speech_file_path)

                # Create a new presentation
                prs = Presentation()

                # Set the background color of the slides
                slide_background = RGBColor(0xD5, 0xE1, 0xDD)  # Mint cream color

                # Add a slide with a title and content layout
                slide_layout = prs.slide_layouts[1]
                slide = prs.slides.add_slide(slide_layout)
                slide.background.fill.solid()
                slide.background.fill.fore_color.rgb = slide_background

                # Add a title and content to the slide
                title = slide.shapes.title
                title.text = slide_title
                title.text_frame.paragraphs[0].font.bold = True  # Make the title bold
                title.text_frame.paragraphs[0].font.color.rgb = RGBColor(0,0,0)  # black color
                title.text_frame.paragraphs[0].font.size = Pt(28)  # Increase font size

                content = slide.placeholders[1]
                content.text = short_description
                content.text_frame.paragraphs[0].font.size = Pt(18)  # Set the font size to 18
                content.text_frame.paragraphs[0].font.color.rgb = RGBColor(0x2E, 0x64, 0x4E)  # Forest green color

                # Add a gradient fill to the title shape
                fill = title.fill
                fill.gradient()
                fill.gradient_stops[0].color.rgb = RGBColor(0x9F, 0xDA, 0xC9)  # Light green
                fill.gradient_stops[1].color.rgb = RGBColor(0x2E, 0x64, 0x4E)  # Dark green

                # Add a shadow effect to the content shape
                content.shadow.inherit = False
                content.shadow.visible = True
                content.shadow.blur_radius = Pt(5)
                content.shadow.offset_x = Inches(0.1)
                content.shadow.offset_y = Inches(0.1)

                # Save the presentation
                presentation_path = "session_folder/presentation.pptx"
                prs.save(presentation_path)

                # Convert the presentation to PDF
                output_directory = 'session_folder'
                os.system(f'libreoffice --headless --convert-to pdf --outdir {output_directory} {presentation_path}')

                pdf_path = "session_folder/presentation.pdf"
                audio_path = "session_folder/audio.mp3"
                images = convert_from_path(pdf_path)
                image_files = []
                for i, img in enumerate(images):
                    img_path = f"session_folder/slide_{i}.png"
                    img.save(img_path, "PNG")
                    image_files.append(img_path)
                audio_clip = AudioFileClip(audio_path)
                video_clip = ImageSequenceClip(image_files, durations=[6]*len(images))
                video_clip = video_clip.set_audio(audio_clip)
                video_clip.fps = 24 
                output_path = f"session_folder/vid{k}.mp4"
                video_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
                for img_file in image_files:
                    os.remove(img_file)
            

            import streamlit as st

        
            st.title("Individual Clips Player")

          
            for i in range(0,100):
                try:
                    video_path = f"session_folder/vid{i}.mp4"
                    with open(video_path, "rb") as f:
                        video_bytes = f.read()
                    st.video(video_bytes, format="video/mp4")
                except:
                    break

            video_clips = []
            for i in range(0, 100):
                try:
                    video_path = f"session_folder/vid{i}.mp4"
                    video_clips.append(VideoFileClip(video_path))
                except:
                    break

            final_clip = concatenate_videoclips(video_clips)
            final_clip.write_videofile("session_folder/final.mp4")

            st.title("Final Video Player")
            final_video_path = "session_folder/final.mp4"
            with open(final_video_path, "rb") as f:
                video_bytes = f.read()
            st.video(video_bytes, format="video/mp4")
    
    
    st.header('Audio Speed')
    st.text('Audio at 1x speed (default)')
    audio_file = open('quality_1.mp3', 'rb')
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format='audio/mp3', start_time=0)
    st.text('Audio at 1.25x speed')
    audio_file = open('quality_1.25.mp3', 'rb')
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format='audio/mp3', start_time=0)
    st.text('Audio at 0.75x speed')
    audio_file = open('quality_0.75.mp3', 'rb')
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format='audio/mp3', start_time=0)
    st.header("voices")
    st.text("Alloy (default)")
    audio_file = open('quality_1.mp3', 'rb')
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format='audio/mp3', start_time=0)
    st.text("Echo")
    audio_file = open('quality_1_echo.mp3', 'rb')
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format='audio/mp3', start_time=0)
    st.text("Fable")
    audio_file = open('quality_1_fable.mp3', 'rb')
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format='audio/mp3', start_time=0) 
    st.text("Onyx")
    audio_file = open('quality_1_onyx.mp3', 'rb')
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format='audio/mp3', start_time=0)
    st.text("Nova")
    audio_file = open('quality_1_nova.mp3', 'rb')
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format='audio/mp3', start_time=0)
    st.text("Shimmer")
    audio_file = open('quality_1_shimmer.mp3', 'rb')
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format='audio/mp3', start_time=0)

    st.markdown("""
    ---
    *A Product from [Eklavya.me](https://eklavya.me)*

    [🔗 LinkedIn](https://www.linkedin.com/company/eklavya-me/)
    """)


if __name__ == '__main__':
    app()
