import json
import os
from openai import OpenAI

# Get OpenAI API key from environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Initialize OpenAI client if API key is available, otherwise set to None
openai = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def get_ai_consultation(question):
    """
    Get AI consultation response for beauty and medical questions
    """
    if not openai or not OPENAI_API_KEY:
        return "متأسفانه در حال حاضر سرویس پاسخگویی هوشمند فعال نیست. لطفاً با پشتیبانی تماس بگیرید."
    
    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """شما یک متخصص پوست و زیبایی هستید. 
                    به سوالات مراجعان در مورد مراقبت از پوست، مو، زیبایی و درمان‌های مختلف پاسخ دهید.
                    پاسخ‌های شما باید دقیق، علمی و در عین حال قابل فهم برای عموم باشد.
                    اگر پاسخ دقیق به سوالی را نمی‌دانید، به جای حدس زدن، صادقانه بگویید که نیاز به مشاوره با پزشک است.
                    همیشه پاسخ ها را به زبان فارسی بدهید.
                    پاسخ های کوتاه و مفید ارائه دهید (حداکثر 3 پاراگراف).
                    تذکر: تمامی پاسخ‌ها جنبه آموزشی دارند و جایگزین مشاوره پزشکی حضوری نیستند."""
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"Error in AI consultation: {e}")
        return "متأسفانه در حال حاضر امکان پاسخگویی به سوال شما وجود ندارد. لطفاً دوباره تلاش کنید."

def generate_beauty_news(topic):
    """
    Generate beauty news article based on a topic
    Returns a tuple of (title, content)
    """
    if not openai or not OPENAI_API_KEY:
        return "سرویس تولید محتوا فعال نیست", "متأسفانه در حال حاضر سرویس تولید محتوا فعال نیست. لطفاً با پشتیبانی تماس بگیرید."
    
    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """شما یک نویسنده متخصص در زمینه سلامت، زیبایی و پوست و مو هستید. 
                    یک مقاله کوتاه در مورد موضوع داده شده بنویسید.
                    مقاله باید شامل یک عنوان جذاب و محتوای علمی اما قابل فهم برای عموم باشد.
                    محتوا باید حداقل 3 پاراگراف و حداکثر 5 پاراگراف داشته باشد.
                    محتوا باید شامل اطلاعات مفید، نکات کاربردی و توصیه‌های علمی باشد.
                    پاسخ را در قالب JSON با دو فیلد "title" و "content" برگردانید.
                    همیشه به زبان فارسی بنویسید."""
                },
                {
                    "role": "user",
                    "content": f"موضوع مقاله: {topic}"
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=1000
        )
        
        result = json.loads(response.choices[0].message.content)
        return result["title"], result["content"]
    
    except Exception as e:
        print(f"Error generating beauty news: {e}")
        return "خطا در تولید محتوا", "متأسفانه در تولید محتوای درخواستی خطایی رخ داده است. لطفاً دوباره تلاش کنید."
