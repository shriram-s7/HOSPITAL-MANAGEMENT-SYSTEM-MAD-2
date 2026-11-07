<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2 class="text-primary">Patient Dashboard</h2>
    </div>
    <ul class="nav nav-tabs mb-4">
      <li class="nav-item">
        <a class="nav-link" :class="{active: view == 'book'}" @click="view = 'book'" href="#">Book Appointment</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" :class="{active: view == 'history'}" @click="view = 'history'" href="#">My History</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" :class="{active: view == 'profile'}" @click="view = 'profile'" href="#">My Profile</a>
      </li>
    </ul>
    <div v-if="view == 'book'">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h4 class="mb-0">Available Doctors</h4>
        <div class="w-50">
          <input type="text" class="form-control" v-model="doctorSearch" placeholder="Search by name or specialization" />
        </div>
      </div>
      <div class="row">
        <div class="col-md-4 mb-3" v-for="d in filteredDoctors" :key="d.id">
          <div class="card p-3 shadow-sm h-100">
            <h5 class="text-dark">{{ d.username }}</h5>
            <p class="text-muted small mb-1">{{ d.specialization || 'General' }}</p>
            <p class="text-muted small mb-3">Avail: {{ d.availability || 'Weekdays' }}</p>
            <button class="btn btn-primary btn-sm mt-auto" @click="openBookForm(d)">Book Session</button>
          </div>
        </div>
      </div>
      <div v-if="showBookForm" class="card p-4 mt-3 bg-light border-primary">
        <h5 class="text-primary">Booking with {{ selectedDoctor.username }}</h5>
        <form @submit.prevent="submitBooking">
          <div class="alert alert-info small" v-if="availableDates.length === 0">
            This doctor has not provided availability yet. Please try another doctor.
          </div>
          <div class="row" v-else>
            <div class="col-md-6 mb-2">
              <label class="form-label">Select Date</label>
              <select v-model="booking.date" class="form-select" required @change="booking.slot = ''">
                <option disabled value="">Choose a date</option>
                <option v-for="d in availableDates" :key="d" :value="d">{{ d }}</option>
              </select>
            </div>
            <div class="col-md-6 mb-2" v-if="booking.date">
              <label class="form-label">Select Shift</label>
              <select v-model="booking.slot" class="form-select" required>
                <option disabled value="">Choose shift</option>
                <option v-for="s in doctorSlots[booking.date]" :key="s" :value="s">{{ s }} ({{ shiftTimesText[s] }})</option>
              </select>
            </div>
          </div>
          <div v-if="bookError" class="text-danger small my-2">{{ bookError }}</div>
          <button class="btn btn-primary btn-sm mt-2" :disabled="!booking.slot">Confirm Booking</button>
          <button type="button" class="btn btn-secondary btn-sm mt-2 ms-2" @click="showBookForm = false">Cancel</button>
        </form>
      </div>
    </div>
    <div v-if="view == 'history'">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h4 class="mb-0">My Appointments</h4>
        <button class="btn btn-outline-success" @click="triggerCSVExport">Export History as CSV</button>
      </div>
      <div v-for="a in appointments" :key="a.id" class="card p-3 mb-3 border-start border-4" :class="a.status == 'Booked' ? 'border-primary' : (a.status == 'Completed' ? 'border-success' : 'border-danger')">
        <div class="d-flex justify-content-between">
          <h5>Dr. {{ a.doctor }}</h5>
          <span class="badge bg-secondary">{{ a.date }} {{ a.time }}</span>
        </div>
        <div class="d-flex justify-content-between align-items-center">
            <p class="mb-1 text-muted">Status: <strong>{{ a.status }}</strong></p>
            <button v-if="a.status == 'Booked'" class="btn btn-outline-danger btn-sm" @click="cancelAppointment(a.id)">Cancel</button>
        </div>
        <div v-if="a.treatment" class="mt-3 p-3 bg-light rounded">
          <h6 class="text-success">Treatment Details</h6>
          <p class="mb-1 small"><strong>Diagnosis:</strong> {{ a.treatment.diagnosis }}</p>
          <p class="mb-1 small"><strong>Prescription:</strong> {{ a.treatment.prescription }}</p>
          <p class="mb-1 small"><strong>Notes:</strong> {{ a.treatment.notes }}</p>
        </div>
      </div>
      <div v-if="appointments.length === 0" class="alert alert-info">No history found.</div>
    </div>
    <div v-if="view == 'profile'">
      <h4>Edit Profile</h4>
      <div class="card p-4 col-md-6 border-primary">
        <form @submit.prevent="updateProfile">
          <div class="mb-3">
            <label class="form-label">Contact Number</label>
            <input type="text" v-model="profile.contact_number" class="form-control" placeholder="Phone">
          </div>
          <div class="mb-3">
            <label class="form-label">Address</label>
            <textarea v-model="profile.address" class="form-control" rows="2" placeholder="Address"></textarea>
          </div>
          <div class="mb-3">
            <label class="form-label">Blood Group</label>
            <select v-model="profile.blood_group" class="form-select">
              <option value="">Select Group</option>
              <option value="A+">A+</option><option value="A-">A-</option>
              <option value="B+">B+</option><option value="B-">B-</option>
              <option value="AB+">AB+</option><option value="AB-">AB-</option>
              <option value="O+">O+</option><option value="O-">O-</option>
            </select>
          </div>
          <button class="btn btn-primary">Save Profile</button>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  data() {
    return {
      view: 'book',
      doctors: [],
      appointments: [],
      showBookForm: false,
      selectedDoctor: null,
      booking: { date: '', slot: '' },
      doctorSlots: {},
      bookError: '',
      doctorSearch: '',
      profile: { contact_number: '', address: '', blood_group: '' },
      shiftTimesText: { 'Morning': '09:00', 'Evening': '14:00', 'Night': '19:00' }
    }
  },
  computed: {
    availableDates() {
      return Object.keys(this.doctorSlots).filter(k => this.doctorSlots[k] && this.doctorSlots[k].length > 0).sort()
    },
    minDate() {
      const today = new Date()
      return today.toISOString().split('T')[0]
    },
    maxDate() {
      const d = new Date()
      d.setDate(d.getDate() + 7)
      return d.toISOString().split('T')[0]
    },
    filteredDoctors() {
      const q = this.doctorSearch.toLowerCase()
      return this.doctors.filter(d => 
        d.username.toLowerCase().includes(q) || 
        (d.specialization && d.specialization.toLowerCase().includes(q))
      )
    }
  },
  mounted() {
    this.fetchData()
    this.fetchProfile()
  },
  methods: {
    getHeaders() {
      return { 
        headers: { 
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        } 
      }
    },
    async fetchData() {
      let d = await axios.get('http://127.0.0.1:5000/api/patient/doctors', this.getHeaders())
      this.doctors = d.data
      let a = await axios.get('http://127.0.0.1:5000/api/patient/appointments', this.getHeaders())
      this.appointments = a.data
    },
    async fetchProfile() {
      let p = await axios.get('http://127.0.0.1:5000/api/patient/profile', this.getHeaders())
      this.profile = p.data
    },
    async updateProfile() {
      await axios.put('http://127.0.0.1:5000/api/patient/profile', this.profile, this.getHeaders())
      alert('Profile updated')
    },
    openBookForm(doc) {
      this.selectedDoctor = doc
      this.booking = { date: '', slot: '' }
      this.bookError = ''
      let parsed = {}
      if (doc.availability) {
        try { parsed = JSON.parse(doc.availability) } catch(e) {}
      }
      this.doctorSlots = parsed
      this.showBookForm = true
    },
    async submitBooking() {
      this.bookError = ''
      const timeSend = this.shiftTimesText[this.booking.slot]
      try {
        await axios.post('http://127.0.0.1:5000/api/patient/appointments', {
          doctor_id: this.selectedDoctor.id,
          date: this.booking.date,
          time: timeSend
        }, this.getHeaders())
        this.showBookForm = false
        this.fetchData()
        this.view = 'history'
      } catch (err) {
        this.bookError = err.response?.data?.msg || 'Booking failed'
      }
    },
    async cancelAppointment(id) {
        if(confirm('Are you sure you want to cancel this appointment?')){
            await axios.put(`http://127.0.0.1:5000/api/patient/appointments/${id}/cancel`, {}, this.getHeaders())
            this.fetchData()
        }
    },
    async triggerCSVExport() {
      try {
        const res = await axios.get('http://127.0.0.1:5000/api/patient/export/download', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          responseType: 'blob'
        })
        const url = window.URL.createObjectURL(new Blob([res.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', 'treatment_history.csv')
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
      } catch(err) {
        alert('No completed appointments found or export failed.')
      }
    }
  }
}
</script>
