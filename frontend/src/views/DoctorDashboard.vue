<template>
  <div>
    <h2 class="mb-4 text-primary">Doctor Dashboard</h2>
    <h5>Your Appointments</h5>
    <div class="row">
      <div class="col-md-6 mb-3" v-for="a in appointments" :key="a.id">
        <div class="card p-3 border-start border-4" :class="a.status == 'Booked' ? 'border-primary' : (a.status == 'Completed' ? 'border-success' : 'border-danger')">
          <div class="d-flex justify-content-between">
            <h5 class="mb-1 text-dark">{{ a.patient }}</h5>
            <span class="badge bg-secondary">{{ a.date }} {{ a.time }}</span>
          </div>
          <p class="text-muted mb-2">Status: <strong>{{ a.status }}</strong></p>
          <button v-if="a.status == 'Booked'" class="btn btn-sm btn-outline-success" @click="openTreatmentForm(a.id)">Add Treatment</button>
          <button v-if="a.status == 'Booked'" class="btn btn-sm btn-outline-danger ms-2" @click="cancelAppointment(a.id)">Cancel Appt</button>
          <button class="btn btn-sm btn-info ms-2 text-white" @click="viewHistory(a.patient_id, a.patient)">Patient History</button>
        </div>
      </div>
    </div>
    <div v-if="appointments.length === 0" class="alert alert-info mt-3">No appointments scheduled.</div>
    <div class="card mt-4 p-4 mb-4">
      <h5 class="text-primary mb-3">My Availability for next 7 days</h5>
      <form @submit.prevent="updateAvailability">
        <div class="table-responsive">
          <table class="table table-bordered table-sm text-center align-middle">
            <thead class="table-light">
              <tr>
                <th>Date</th>
                <th>Morning <br><small class="text-muted">(8AM-1PM)</small></th>
                <th>Evening <br><small class="text-muted">(1PM-6PM)</small></th>
                <th>Night <br><small class="text-muted">(6PM-11PM)</small></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="d in nextSevenDays" :key="d.date">
                <td class="fw-bold">{{ d.display }}</td>
                <td><input type="checkbox" class="form-check-input" v-model="selectedSlots[d.date]" value="Morning" /></td>
                <td><input type="checkbox" class="form-check-input" v-model="selectedSlots[d.date]" value="Evening" /></td>
                <td><input type="checkbox" class="form-check-input" v-model="selectedSlots[d.date]" value="Night" /></td>
              </tr>
            </tbody>
          </table>
        </div>
        <button class="btn btn-primary mt-2">Update Availability</button>
      </form>
    </div>
    <div v-if="showHistory" class="card mt-4 p-4 border-info">
      <div class="d-flex justify-content-between mb-3">
        <h5 class="text-info">Medical History: {{ selectedPatientName }}</h5>
        <button type="button" class="btn btn-close" @click="showHistory = false"></button>
      </div>
      <div v-if="history.length > 0">
        <ul class="list-group">
          <li class="list-group-item" v-for="(h, i) in history" :key="i">
            <strong>{{ h.date }}</strong> - Dr. {{ h.doctor }}<br/>
            <span class="small text-muted">Diagnosis:</span> {{ h.diagnosis }}<br/>
            <span class="small text-muted">Rx:</span> {{ h.prescription }}
          </li>
        </ul>
      </div>
      <p v-else class="text-muted">No past treatments recorded.</p>
    </div>
    <div v-if="showTreatmentForm" class="card mt-4 p-4 border-success">
      <h5 class="text-success">Complete Appointment #{{ activeAppId }}</h5>
      <form @submit.prevent="submitTreatment">
        <div class="mb-2">
          <label class="form-label">Diagnosis</label>
          <textarea v-model="treatment.diagnosis" class="form-control" rows="2" required></textarea>
        </div>
        <div class="mb-2">
          <label class="form-label">Prescription</label>
          <textarea v-model="treatment.prescription" class="form-control" rows="2" required></textarea>
        </div>
        <div class="mb-2">
          <label class="form-label">Additional Notes</label>
          <textarea v-model="treatment.notes" class="form-control" rows="2"></textarea>
        </div>
        <button class="btn btn-success btn-sm">Complete Appointment</button>
        <button type="button" class="btn btn-light btn-sm ms-2" @click="showTreatmentForm = false">Cancel</button>
      </form>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  data() {
    return {
      appointments: [],
      showTreatmentForm: false,
      activeAppId: null,
      treatment: { diagnosis: '', prescription: '', notes: '' },
      showHistory: false,
      history: [],
      selectedPatientName: '',
      selectedSlots: {}
    }
  },
  computed: {
    nextSevenDays() {
      const days = []
      const today = new Date()
      for(let i=0; i<7; i++) {
        let d = new Date(today)
        d.setDate(d.getDate() + i)
        const dateStr = d.toISOString().split('T')[0]
        days.push({
          date: dateStr,
          display: dateStr + ' (' + d.toLocaleDateString('en-US', {weekday: 'short'}) + ')'
        })
      }
      return days
    }
  },
  mounted() {
    this.nextSevenDays.forEach(d => {
      this.selectedSlots[d.date] = []
    })
    this.fetchAppointments()
    this.fetchAvailability()
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
    async fetchAppointments() {
      const res = await axios.get('http://127.0.0.1:5000/api/doctor/appointments', this.getHeaders())
      this.appointments = res.data
    },
    async fetchAvailability() {
      const res = await axios.get('http://127.0.0.1:5000/api/doctor/availability', this.getHeaders())
      if (res.data.availability) {
        try {
          const parsed = JSON.parse(res.data.availability)
          this.nextSevenDays.forEach(d => {
            if (parsed[d.date]) this.selectedSlots[d.date] = parsed[d.date]
          })
        } catch(e) {}
      }
    },
    async updateAvailability() {
      const trimmedSlots = {}
      this.nextSevenDays.forEach(d => {
        trimmedSlots[d.date] = this.selectedSlots[d.date] || []
      })
      const compactStr = JSON.stringify(trimmedSlots)
      await axios.post('http://127.0.0.1:5000/api/doctor/availability', { availability: compactStr }, this.getHeaders())
      alert('Availability updated!')
    },
    async cancelAppointment(id) {
      if(confirm('Cancel this appointment?')) {
        await axios.put(`http://127.0.0.1:5000/api/doctor/appointments/${id}/status`, {status: 'Cancelled'}, this.getHeaders())
        this.fetchAppointments()
      }
    },
    async viewHistory(patientId, patientName) {
      this.selectedPatientName = patientName
      const res = await axios.get(`http://127.0.0.1:5000/api/doctor/patients/${patientId}/history`, this.getHeaders())
      this.history = res.data
      this.showHistory = true
      this.showTreatmentForm = false
    },
    openTreatmentForm(id) {
      this.activeAppId = id
      this.treatment = { diagnosis: '', prescription: '', notes: '' }
      this.showTreatmentForm = true
    },
    async submitTreatment() {
      await axios.post(`http://127.0.0.1:5000/api/doctor/appointments/${this.activeAppId}/treatment`, this.treatment, this.getHeaders())
      this.showTreatmentForm = false
      this.fetchAppointments()
    }
  }
}
</script>
