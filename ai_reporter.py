# ai_reporter.py
import pandas as pd
from db_connector import execute_query
from config import GEMINI_API_KEY, AI_MODEL
from google import genai
from google.genai.errors import APIError

def analyze_compliance_data():
    """
    يجلب البيانات من سجلات الامتثال ويقوم بتحليلها باستخدام Pandas.
    """
    print("\n--- تحليل بيانات الامتثال ---")
    
    # جلب جميع سجلات عدم الامتثال من آخر 30 يوماً
    logs = execute_query(
        """
        SELECT 
            cl.compliance_status, 
            cl.checked_at, 
            u.full_name, 
            u.department,
            cl.notes
        FROM compliance_logs cl
        JOIN users u ON cl.user_id = u.user_id
        WHERE cl.compliance_status = 'non_compliant' AND cl.checked_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """,
        fetch=True
    )
    
    if not logs:
        print("لا توجد سجلات عدم امتثال حديثة للتحليل.")
        return None

    df = pd.DataFrame(logs)
    
    # 1. تحليل إجمالي: عدد حالات عدم الامتثال حسب القسم
    compliance_by_dept = df.groupby('department').size().sort_values(ascending=False).to_dict()
    
    # 2. تحليل النوع: ملخص لأكثر المشكلات تكراراً (بناءً على أول كلمة في الـ notes)
    df['policy_type'] = df['notes'].apply(lambda x: x.split()[2] if x else 'غير محدد')
    top_issues = df.groupby('policy_type').size().sort_values(ascending=False).to_dict()
    
    analysis_results = {
        "Total_Non_Compliant_Records": len(df),
        "Last_30_Days_Summary": f"تم تسجيل {len(df)} حالة عدم امتثال في آخر 30 يوماً.",
        "Compliance_by_Department": compliance_by_dept,
        "Top_Violated_Policies": top_issues
    }
    
    print("نتائج التحليل الأولي (Pandas):")
    print(analysis_results)
    
    return analysis_results

def generate_ai_report(analysis_data):
    """
    يرسل نتائج التحليل إلى نموذج Gemini لإنشاء تقرير احترافي.
    """
    if analysis_data is None:
        return "لا يمكن توليد تقرير لعدم وجود بيانات تحليلية."

    print("\n--- توليد تقرير الذكاء الاصطناعي ---")
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        prompt = f"""
        بصفتك محلل امتثال أمني محترف، قم بإنشاء تقرير تنفيذي موجز (Executive Summary) بناءً على بيانات التحليل التالية. 
        يجب أن يكون التقرير باللغة العربية، احترافياً، ومنسقاً بشكل جيد (استخدم Markdown).
        
        ركز على:
        1. ملخص تنفيذي (Executive Summary): لخص الوضع العام.
        2. المناطق الأكثر عرضة للمخاطر: (الأقسام التي بها أعلى نسبة عدم امتثال).
        3. أهم الانتهاكات: (كلمات المرور مقابل النسخ الاحتياطي).
        4. توصيات فورية: حدد 3 إجراءات فورية للحد من المخاطر.

        بيانات التحليل:
        {analysis_data}
        """

        response = client.models.generate_content(
            model=AI_MODEL,
            contents=prompt
        )
        
        return response.text

    except APIError as e:
        return f"خطأ في الاتصال بنموذج الذكاء الاصطناعي (Gemini): تأكد من مفتاح API. الخطأ: {e}"
    except Exception as e:
        return f"حدث خطأ غير متوقع: {e}"
