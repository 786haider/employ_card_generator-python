import streamlit as st
import qrcode
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import hashlib
from datetime import datetime
import uuid

class EmployeeCardGenerator:
    def __init__(self):
        # Initialize session state
        if 'employees' not in st.session_state:
            st.session_state.employees = pd.DataFrame(columns=[
                'Unique ID', 'Name', 'CNIC', 'Age', 'Role', 'City', 'Shift', 'Photo'
            ])
        
        if 'attendance' not in st.session_state:
            st.session_state.attendance = pd.DataFrame(columns=[
                'Unique ID', 'Name', 'Date', 'Time', 'Timestamp'
            ])
        
        # Set up admin credentials
        self.ADMIN_PASSWORD = 'Haider786'

    def generate_unique_id(self):
        """Generate a unique ID for each employee"""
        while True:
            # Generate a unique ID (e.g., AT-001, AT-002)
            unique_id = f'AT-{len(st.session_state.employees) + 1:03d}'
            
            # Check if ID already exists
            if not st.session_state.employees['Unique ID'].eq(unique_id).any():
                return unique_id

    def generate_qr_code(self, employee_data):
        """Generate QR code with employee information"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        # Include Unique ID in QR code data
        qr_data = "\n".join([f"{key}: {value}" for key, value in employee_data.items()])
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        return qr_img

    def create_employee_card(self, employee_data, logo_path, employee_photo):
        """Create a professional employee card"""
        # Card dimensions
        card_width, card_height = 1054, 640
        
        # Create card background
        card = Image.new('RGB', (card_width, card_height), color='white')
        draw = ImageDraw.Draw(card)
        
        # Load fonts
        try:
            title_font = ImageFont.truetype("arial.ttf", 40)
            label_font = ImageFont.truetype("arial.ttf", 30)
            data_font = ImageFont.truetype("arial.ttf", 35)
        except IOError:
            # Fallback to default font
            title_font = ImageFont.load_default()
            label_font = ImageFont.load_default()
            data_font = ImageFont.load_default()
        
        # Company logo
        try:
            logo = Image.open(logo_path)
            logo = logo.resize((250, 150))
            card.paste(logo, (50, 50), logo if logo.mode == 'RGBA' else None)
        except Exception as e:
            st.error(f"Error loading logo: {e}")
        
        # Employee Photo
        try:
            if employee_photo:
                photo = Image.open(employee_photo)
                photo = self.crop_to_aspect(photo, 300, 400)
                card.paste(photo, (card_width-350, 150))
        except Exception as e:
            st.error(f"Error loading employee photo: {e}")
            draw.rectangle([card_width-350, 150, card_width-50, 450], 
                           fill='lightgray', outline='black')
            draw.text((card_width-250, 300), "PHOTO", 
                      fill='gray', font=label_font)
        
        # Card Design Colors
        primary_color = (31, 97, 141)  # Dark Blue
        
        # Draw header
        draw.rectangle([0, 0, card_width, 100], fill=primary_color)
        draw.text((300, 30), "ALPHA TECH EMPLOYEE CARD", 
                  fill='white', font=title_font)
        
        # Employee Details
        details = [
            ('Name', employee_data['Name']),
            ('CNIC', employee_data['CNIC']),
            ('Age', str(employee_data['Age'])),
            ('Role', employee_data['Role']),
            ('Unique ID', employee_data['Unique ID']),  # Added Unique ID
            ('City', employee_data['City']),
            ('Shift', employee_data['Shift'])
        ]
        
        start_y = 150
        for i, (label, value) in enumerate(details):
            draw.text((50, start_y + i*50), f"{label}:", 
                      fill=primary_color, font=label_font)
            draw.text((300, start_y + i*50), str(value), 
                      fill='black', font=data_font)
        
        # QR Code Generation
        qr_img = self.generate_qr_code(employee_data)
        qr_img = qr_img.resize((250, 250))
        card.paste(qr_img, (50, card_height-300))
        
        # Footer
        draw.line([(0, card_height-50), (card_width, card_height-50)], 
                  fill=primary_color, width=5)
        
        return card

    def crop_to_aspect(self, image, target_width, target_height):
        """Crop image to specified aspect ratio and resize"""
        img_ratio = image.width / image.height
        target_ratio = target_width / target_height
        
        if img_ratio > target_ratio:
            new_height = image.height
            new_width = int(new_height * target_ratio)
            left = (image.width - new_width) // 2
            top = 0
        else:
            new_width = image.width
            new_height = int(new_width / target_ratio)
            left = 0
            top = (image.height - new_height) // 2
        
        cropped = image.crop((left, top, left+new_width, top+new_height))
        return cropped.resize((target_width, target_height))

    def record_attendance(self, unique_id, name):
        """Record employee attendance"""
        now = datetime.now()
        attendance_record = pd.DataFrame({
            'Unique ID': [unique_id],
            'Name': [name],
            'Date': [now.strftime('%Y-%m-%d')],
            'Time': [now.strftime('%H:%M:%S')],
            'Timestamp': [now]
        })
        
        # Append to existing attendance records
        st.session_state.attendance = pd.concat([
            st.session_state.attendance, 
            attendance_record
        ], ignore_index=True)

    def admin_panel(self):
        """Admin Panel with authentication and features"""
        st.title("🔐 Alpha Tech Admin Panel")
        
        # Admin Authentication
        password = st.text_input("Enter Admin Password", type="password")
        
        if password == self.ADMIN_PASSWORD:
            # Tabs for different admin functionalities
            tab1, tab2, tab3 = st.tabs([
                "Employee Cards", 
                "Attendance Records", 
                "Scan Attendance"
            ])
            
            with tab1:
                st.header("Generated Employee Cards")
                # Display all employee cards
                if not st.session_state.employees.empty:
                    for _, employee in st.session_state.employees.iterrows():
                        # Recreate card
                        card = self.create_employee_card(
                            employee.to_dict(), 
                            "temp_logo.png", 
                            employee.get('Photo')
                        )
                        
                        # Display card
                        st.image(card, caption=f"Card for {employee['Name']}")
                else:
                    st.info("No employee cards generated yet.")
            
            with tab2:
                st.header("Attendance Records")
                if not st.session_state.attendance.empty:
                    # Display attendance with filtering options
                    st.dataframe(st.session_state.attendance)
                    
                    # Optional: Download attendance as CSV
                    csv = st.session_state.attendance.to_csv(index=False)
                    st.download_button(
                        "Download Attendance CSV", 
                        csv, 
                        "attendance_records.csv", 
                        "text/csv"
                    )
                else:
                    st.info("No attendance records available.")
            
            with tab3:
                st.header("Scan Attendance")
                unique_id = st.text_input("Scan/Enter Employee Unique ID")
                
                if st.button("Mark Attendance"):
                    # Find employee by Unique ID
                    employee = st.session_state.employees[
                        st.session_state.employees['Unique ID'] == unique_id
                    ]
                    
                    if not employee.empty:
                        # Record attendance
                        self.record_attendance(
                            unique_id, 
                            employee.iloc[0]['Name']
                        )
                        st.success(f"Attendance marked for {employee.iloc[0]['Name']}")
                    else:
                        st.error("No employee found with this ID")
        else:
            st.warning("Incorrect Admin Password")

    def main_app(self):
        """Main Streamlit Application"""
        st.set_page_config(
            page_title="Alpha Tech Employee Management", 
            page_icon="🏢", 
            layout="wide"
        )
        
        # App Navigation
        app_mode = st.sidebar.selectbox(
            "Choose Application Mode", 
            ["Employee Card Generator", "Admin Panel"]
        )
        
        if app_mode == "Employee Card Generator":
            st.title("🏢 Alpha Tech Employee Card Generator")
            
            with st.sidebar:
                st.header("Employee Details")
                name = st.text_input("Employee Name")
                cnic = st.text_input("CNIC Number")
                age = st.number_input("Age", min_value=18, max_value=65)
                role = st.selectbox("Role", [
                    "Software Engineer", "Data Analyst", "Project Manager", 
                    "HR Specialist", "Sales Executive", "Marketing Coordinator"
                ])
                city = st.text_input("City")
                shift = st.selectbox("Shift", ["Morning", "Afternoon", "Night"])
                
                # Logo Upload
                st.subheader("Company Logo")
                logo = st.file_uploader("Upload Company Logo", type=['png', 'jpg', 'jpeg'])
                
                # Employee Photo Upload
                st.subheader("Employee Photo")
                employee_photo = st.file_uploader("Upload Employee Photo", type=['png', 'jpg', 'jpeg'])
                
                # Generate Card Button
                if st.button("Generate Employee Card"):
                    if name and cnic and logo:
                        # Generate Unique ID
                        unique_id = self.generate_unique_id()
                        
                        # Save uploaded logo temporarily
                        with open("temp_logo.png", "wb") as f:
                            f.write(logo.getbuffer())
                        
                        # Save employee photo if uploaded
                        photo_path = None
                        if employee_photo:
                            photo_path = "temp_employee_photo.png"
                            with open(photo_path, "wb") as f:
                                f.write(employee_photo.getbuffer())
                        
                        # Prepare employee data
                        employee_data = {
                            'Unique ID': unique_id,
                            'Name': name,
                            'CNIC': cnic,
                            'Age': age,
                            'Role': role,
                            'City': city,
                            'Shift': shift
                        }
                        
                        # Add to employees DataFrame
                        new_employee = pd.DataFrame([employee_data])
                        st.session_state.employees = pd.concat([
                            st.session_state.employees, 
                            new_employee
                        ], ignore_index=True)
                        
                        # Create card
                        card = self.create_employee_card(
                            employee_data, 
                            "temp_logo.png", 
                            photo_path
                        )
                        
                        # Display and Download Card
                        buf = io.BytesIO()
                        card.save(buf, format="PNG")
                        byte_im = buf.getvalue()
                        
                        st.image(card, caption="Generated Employee Card")
                        
                        # Download Button
                        st.download_button(
                            label="Download Employee Card",
                            data=byte_im,
                            file_name=f"{unique_id}_{name}_employee_card.png",
                            mime="image/png"
                        )
                    else:
                        st.warning("Please fill all details and upload logo")
        
        else:
            # Admin Panel
            self.admin_panel()

# Run the application
if __name__ == "__main__":
    generator = EmployeeCardGenerator()
    generator.main_app()
    