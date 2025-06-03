document.addEventListener('DOMContentLoaded', function() {
    // Get elements
    const serviceSelect = document.getElementById('service');
    const doctorSelect = document.getElementById('doctor');
    doctorSelect.disabled = false;
    const dateInput = document.getElementById('date');
    const timeSelect = document.getElementById('time');
    
    // Check if we're on the booking page
    if (!serviceSelect || !doctorSelect || !dateInput || !timeSelect) {
        return;
    }
    
    // Initialize Persian datepicker
    if ($.fn.persianDatepicker) {
        $(dateInput).persianDatepicker({
            format: 'YYYY/MM/DD',
            minDate: new persianDate().unix(),
            toolbox: {
                calendarSwitch: {
                    enabled: false
                }
            },
            responsive: true,
            onSelect: function() {
                updateAvailableTimes();
            }
        });
    }
    
    // Event listeners for form elements
    serviceSelect.addEventListener('change', function() {
        updateDoctorOptions();
        clearTimeOptions();
    });
    
    doctorSelect.addEventListener('change', function() {
        updateAvailableTimes();
    });
    
    dateInput.addEventListener('change', function() {
        updateAvailableTimes();
    });
    
    // Update available doctors based on selected service
    function updateDoctorOptions() {
        const serviceId = serviceSelect.value;
        
        if (!serviceId) {
            // Clear doctor options if no service selected
            clearDoctorOptions();
            return;
        }
        
        // Show loading indicator
        doctorSelect.disabled = true;
        doctorSelect.innerHTML = '<option value="">در حال بارگذاری...</option>';
        
        // Fetch doctors who provide this service
        ffetch(`/get_service_doctors?service_id=${serviceId}`)
            .then(res => res.json())
            .then(data => {
            doctorSelect.innerHTML = '<option value="">انتخاب پزشک</option>';
         
                // Add new options
                if (data.doctors && data.doctors.length > 0) {
                    data.doctors.forEach(doctor => {
                        const option = document.createElement('option');
                        option.value = doctor.id;
                        option.textContent = doctor.name;
                        doctorSelect.appendChild(option);
                    });
                    
                    // Enable select
                    doctorSelect.disabled = false;
                } else {
                    doctorSelect.innerHTML = '<option value="">پزشکی برای این خدمت یافت نشد</option>';
                    doctorSelect.disabled = true;
                }
            })
            .catch(error => {
                console.error('Error fetching doctors:', error);
                doctorSelect.innerHTML = '<option value="">خطا در بارگذاری پزشکان</option>';
                doctorSelect.disabled = true;
            });
    }
    
    // Clear doctor options
    function clearDoctorOptions() {
        doctorSelect.innerHTML = '<option value="">ابتدا خدمت را انتخاب کنید</option>';
        doctorSelect.disabled = true;
    }
    
    // Update available times based on selected service, doctor, and date
    function updateAvailableTimes() {
        const serviceId = serviceSelect.value;
        const doctorId = doctorSelect.value;
        const date = dateInput.value;
        
        if (!serviceId || !doctorId || !date) {
            clearTimeOptions();
            return;
        }
        
        // Show loading indicator
        timeSelect.disabled = true;
        timeSelect.innerHTML = '<option value="">در حال بارگذاری...</option>';
        
        // Fetch available times
        fetch(`/get_available_times?service_id=${serviceId}&doctor_id=${doctorId}&date=${date}`)
            .then(response => response.json())
            .then(data => {
                // Clear current options
                timeSelect.innerHTML = '<option value="">انتخاب زمان</option>';
                
                const now = new Date();
                const selectedDate = new Date(date); // تاریخ انتخاب شده
            
                if (data.available_times && data.available_times.length > 0) {
                    data.available_times.forEach(time => {
                        // ساختن یک شی Date برای هر زمان برای مقایسه
                        const [hours, minutes] = time.split(':').map(Number);
                        const timeDate = new Date(selectedDate);
                        timeDate.setHours(hours, minutes, 0, 0);
            
                        // فقط زمان‌هایی که بزرگتر یا مساوی الان هستن
                        if (timeDate >= now) {
                            const option = document.createElement('option');
                            option.value = time;
                            option.textContent = time;
                            timeSelect.appendChild(option);
                        }
                    });
                    
                    // اگه هیچ گزینه‌ای اضافه نشد، پیام بده
                    if (timeSelect.options.length === 1) { // فقط گزینه پیش‌فرض هست
                        timeSelect.innerHTML = '<option value="">زمان خالی برای این تاریخ وجود ندارد</option>';
                        timeSelect.disabled = true;
                    } else {
                        timeSelect.disabled = false;
                    }
                } else {
                    timeSelect.innerHTML = '<option value="">زمان خالی برای این تاریخ وجود ندارد</option>';
                    timeSelect.disabled = true;
                }
            })
            .catch(error => {
                console.error('Error fetching available times:', error);
                timeSelect.innerHTML = '<option value="">خطا در بارگذاری زمان‌ها</option>';
                timeSelect.disabled = true;
            });
    }
    
    // Clear time options
    function clearTimeOptions() {
        timeSelect.innerHTML = '<option value="">ابتدا خدمت، پزشک و تاریخ را انتخاب کنید</option>';
        timeSelect.disabled = true;
    }
    
    // Initialize form
    clearDoctorOptions();
    clearTimeOptions();
});
