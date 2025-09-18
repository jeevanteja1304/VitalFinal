from fpdf import FPDF
import datetime
import os

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'VitalLens Health Report', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_report(username, vital_signs):
    """Generates a PDF report with the user's vital signs."""
    
    report_path = os.path.join('reports', f'report_{username}_{datetime.date.today()}.pdf')
    os.makedirs('reports', exist_ok=True)
    
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', '', 12)
    
    # Report Details
    pdf.cell(0, 10, f"Patient Name: {username.capitalize()}", 0, 1)
    pdf.cell(0, 10, f"Date of Measurement: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1)
    pdf.ln(10)

    # Vitals Table
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(60, 10, 'Metric', 1, 0, 'C')
    pdf.cell(60, 10, 'Value', 1, 1, 'C')
    
    pdf.set_font('Arial', '', 12)
    pdf.cell(60, 10, 'Heart Rate', 1, 0)
    pdf.cell(60, 10, f"{vital_signs['heart_rate']} bpm", 1, 1)
    
    pdf.cell(60, 10, 'Systolic BP', 1, 0)
    pdf.cell(60, 10, f"{vital_signs['systolic_bp']} mmHg", 1, 1)

    pdf.cell(60, 10, 'Diastolic BP', 1, 0)
    pdf.cell(60, 10, f"{vital_signs['diastolic_bp']} mmHg", 1, 1)
    
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 10)
    pdf.multi_cell(0, 5, 'Disclaimer: This report is generated based on a non-contact iPPG measurement and is for informational purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment.')

    pdf.output(report_path)
    return report_path