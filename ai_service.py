from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai = OpenAI(api_key=OPENAI_API_KEY)

def get_ai_consultation(question):
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "شما یک مشاور زیبایی هستید. به سوالات به صورت دقیق، کوتاه و مفید پاسخ دهید. پاسخ‌ها آموزشی هستند و جایگزین مشاوره پزشکی نیستند."},
                {"role": "user", "content": question}
            ],
            max_tokens=500
        )
        return response.choices[0].message.content

    except Exception as e:
        print(f"خطا در اتصال به OpenAI: {e}")
        return "متأسفانه در حال حاضر امکان پاسخگویی به سوال شما وجود ندارد. لطفاً دوباره تلاش کنید."
    
def generate_beauty_news(topic):
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5",  
            messages=[
                {
                    "role": "system",
                    "content": "شما یک نویسنده تخصصی مقالات پزشکی و زیبایی هستید. درباره موضوعات پیشنهادی مقالات علمی و قابل فهم برای عموم بنویسید."
                },
                {
                    "role": "user",
                    "content": f"لطفا یک مقاله کامل درباره موضوع «{topic}» بنویس. فقط عنوان و متن مقاله را بده."
                }
            ],
            max_tokens=1000
        )

        content = response.choices[0].message.content.strip()

        # فرض: خروجی شامل یک خط عنوان و بعدش متن مقاله‌ست
        lines = content.split('\n', 1)
        title = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""

        return title, body

    except Exception as e:
        print(f"AI article generation error: {e}")
        return "خطا در تولید مقاله", "متأسفانه تولید مقاله با مشکل مواجه شد."