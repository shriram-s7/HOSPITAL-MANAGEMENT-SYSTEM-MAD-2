<template>
  <div>
    <h2 class="mb-4 text-primary">Admin Dashboard</h2>
    <div class="row mb-4">
      <div class="col-md-4">
        <div class="card bg-primary text-white p-3 text-center">
          <h4>{{ stats.doctors }}</h4>
          <span>Total Doctors</span>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card bg-success text-white p-3 text-center">
          <h4>{{ stats.patients }}</h4>
          <span>Total Patients</span>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card bg-info text-white p-3 text-center">
          <h4>{{ stats.appointments }}</h4>
          <span>Total Appointments</span>
        </div>
      </div>
      <div class="row mt-4">
        <div class="col-md-12">
          <div class="card p-3 border-danger">
             <h5 class="text-danger">Admin Development Testing Links</h5>
             <div>
               <button class="btn btn-sm btn-outline-warning text-dark me-2" @click="testDailyReminders">Fire Daily Reminders Job</button>
               <button class="btn btn-sm btn-outline-warning text-dark" @click="testMonthlyJob">Fire Monthly Reports Job</button>
             </div>
          </div>
        </div>
      </div>
    </div>
    <ul class="nav nav-tabs mb-4">
      <li class="nav-item">
        <a class="nav-link" :class="{active: view == 'doctors'}" @click="view = 'doctors'" href="#">Manage Doctors</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" :class="{active: view == 'appointments'}" @click="view = 'appointments'" href="#">Appointments</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" :class="{active: view == 'patients'}" @click="view = 'patients'" href="#">Search Patients</a>
      </li>
    </ul>
    <div v-if="view == 'doctors'">
      <div class="d-flex justify-content-between mb-3 align-items-center">
        <h4>Doctors List</h4>
        <input type="text" class="form-control w-25" v-model="doctorSearch" placeholder="Search by name or spec" />
        <button class="btn btn-sm btn-primary" @click="showAddDoctor = !showAddDoctor">
          {{ showAddDoctor ? 'Close Form' : 'Add New Doctor' }}
        </button>
      </div>
      <div class="card p-3 mb-4" v-if="showAddDoctor">
        <form @submit.prevent="addDoctor">
          <div class="row">
            <div class="col-md-3 mb-2"><input v-model="newDoc.username" placeholder="Username" class="form-control" required/></div>
            <div class="col-md-3 mb-2"><input v-model="newDoc.password" placeholder="Password" type="password" class="form-control" required/></div>
            <div class="col-md-3 mb-2"><input v-model="newDoc.email" placeholder="Email" class="form-control"/></div>
            <div class="col-md-3 mb-2"><input v-model="newDoc.specialization" placeholder="Specialization" class="form-control"/></div>
          </div>
          <button class="btn btn-primary btn-sm mt-2">Save Doctor</button>
        </form>
      </div>
      <table class="table table-hover bg-white rounded shadow-sm">
        <thead class="table-light">
          <tr><th>ID</th><th>Name</th><th>Email</th><th>Specialization</th><th>Actions</th></tr>
        </thead>
        <tbody>
          <tr v-for="d in filteredDoctors" :key="d.id">
            <td>{{ d.id }}</td>
            <td>{{ d.username }}</td>
            <td>{{ d.email }}</td>
            <td>{{ d.specialization }}</td>
            <td>
              <button class="btn btn-sm btn-info me-2 text-white" @click="openEditDoctor(d)">Edit</button>
              <button class="btn btn-sm btn-danger" @click="deleteDoctor(d.id)">Remove</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="view == 'appointments'">
      <h4>All Appointments</h4>
      <table class="table table-hover bg-white rounded shadow-sm">
        <thead class="table-light">
          <tr><th>ID</th><th>Patient</th><th>Doctor</th><th>Date</th><th>Time</th><th>Status</th></tr>
        </thead>
        <tbody>
          <tr v-for="a in appointments" :key="a.id">
            <td>{{ a.id }}</td>
            <td>{{ a.patient }}</td>
            <td>{{ a.doctor }}</td>
            <td>{{ a.date }}</td>
            <td>{{ a.time }}</td>
            <td>
              <span class="badge" :class="{'bg-warning': a.status == 'Booked', 'bg-success': a.status == 'Completed', 'bg-danger': a.status == 'Cancelled'}">
                {{ a.status }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="editDocId" class="card mt-4 p-4 border-info">
      <h5 class="text-info">Edit Doctor: {{ editDoc.username }}</h5>
      <form @submit.prevent="submitEditDoctor">
        <div class="row">
          <div class="col-md-3">
            <label class="form-label">Username</label>
            <input type="text" v-model="editDoc.username" class="form-control" required>
          </div>
          <div class="col-md-3">
            <label class="form-label">Email</label>
            <input type="email" v-model="editDoc.email" class="form-control" required>
          </div>
          <div class="col-md-3">
            <label class="form-label">Specialization</label>
            <input type="text" v-model="editDoc.specialization" class="form-control" required>
          </div>
          <div class="col-md-3 d-flex align-items-end">
            <button class="btn btn-info w-100 text-white">Save Changes</button>
            <button type="button" class="btn btn-secondary ms-2" @click="editDocId = null">Cancel</button>
          </div>
        </div>
      </form>
    </div>
    <div v-if="view == 'patients'">
      <h4>Search Patients</h4>
      <input type="text" class="form-control w-50 mb-3" v-model="patientSearch" @input="fetchPatients" placeholder="Search by username, ID, or contact..."/>
      <ul class="list-group w-50">
        <li class="list-group-item d-flex justify-content-between align-items-center" v-for="p in patients" :key="p.id">
          <span>ID: {{ p.id }} | <strong>{{ p.username }}</strong> <span v-if="p.contact" class="text-muted small">({{ p.contact }})</span></span>
          <div>
            <button class="btn btn-sm btn-info text-white me-2" @click="openEditPatient(p)">Edit</button>
            <button class="btn btn-sm btn-danger" @click="deletePatient(p.id)">Remove</button>
          </div>
        </li>
      </ul>
    </div>
    <div v-if="editPatId" class="card mt-4 p-4 border-info">
      <h5 class="text-info">Edit Patient Info: {{ editPat.username }}</h5>
      <form @submit.prevent="submitEditPatient">
        <div class="row">
          <div class="col-md-4">
            <label class="form-label">Username</label>
            <input type="text" v-model="editPat.username" class="form-control" required>
          </div>
          <div class="col-md-4">
            <label class="form-label">Contact</label>
            <input type="text" v-model="editPat.contact" class="form-control" placeholder="Optional">
          </div>
          <div class="col-md-4 d-flex align-items-end">
            <button class="btn btn-info w-100 text-white">Save Changes</button>
            <button type="button" class="btn btn-secondary ms-2" @click="editPatId = null">Cancel</button>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  data() {
    return {
      stats: { doctors: 0, patients: 0, appointments: 0 },
      view: 'doctors',
      doctors: [],
      appointments: [],
      patients: [],
      patientSearch: '',
      doctorSearch: '',
      showAddDoctor: false,
      newDoc: { username: '', password: '', email: '', specialization: '' },
      editDocId: null,
      editDoc: { username: '', email: '', specialization: '' },
      editPatId: null,
      editPat: { username: '', contact: '' }
    }
  },
  computed: {
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
      const h = this.getHeaders()
      let s = await axios.get('http://127.0.0.1:5000/api/admin/dashboard', h)
      this.stats = s.data
      let d = await axios.get('http://127.0.0.1:5000/api/admin/doctors', h)
      this.doctors = d.data
      let a = await axios.get('http://127.0.0.1:5000/api/admin/appointments', h)
      this.appointments = a.data
      await this.fetchPatients()
    },
    async fetchPatients() {
      const res = await axios.get(`http://127.0.0.1:5000/api/admin/patients?search=${this.patientSearch}`, this.getHeaders())
      this.patients = res.data
    },
    async addDoctor() {
      try {
        await axios.post('http://127.0.0.1:5000/api/admin/doctors', this.newDoc, this.getHeaders())
        this.newDoc = { username: '', password: '', email: '', specialization: '' }
        this.showAddDoctor = false
        this.fetchData()
      } catch (err) {
        alert(err.response?.data?.msg || 'Failed to add doctor')
      }
    },
    async deleteDoctor(id) {
      if(confirm('Are you sure you want to remove this doctor?')) {
        await axios.delete(`http://127.0.0.1:5000/api/admin/doctors/${id}`, this.getHeaders())
        this.fetchData()
      }
    },
    openEditDoctor(doc) {
      this.editDocId = doc.id
      this.editDoc = { username: doc.username, email: doc.email, specialization: doc.specialization }
    },
    async submitEditDoctor() {
      try {
        await axios.put(`http://127.0.0.1:5000/api/admin/doctors/${this.editDocId}`, this.editDoc, this.getHeaders())
        this.editDocId = null
        this.fetchData()
      } catch (err) {
        alert('Failed to update doctor')
      }
    },
    async deletePatient(id) {
      if(confirm('Are you sure you want to completely remove this patient and their history?')) {
        await axios.delete(`http://127.0.0.1:5000/api/admin/patients/${id}`, this.getHeaders())
        this.fetchPatients()
        this.fetchData()
      }
    },
    openEditPatient(pat) {
      this.editPatId = pat.id
      this.editPat = { username: pat.username, contact: pat.contact || '' }
    },
    async submitEditPatient() {
      try {
        await axios.put(`http://127.0.0.1:5000/api/admin/patients/${this.editPatId}`, this.editPat, this.getHeaders())
        this.editPatId = null
        this.fetchPatients()
      } catch (err) {
        alert('Failed to update patient')
      }
    },
    async testDailyReminders() {
      try { 
        let res = await axios.post('http://127.0.0.1:5000/api/admin/test/daily-reminders', {}, this.getHeaders())
        alert(res.data.msg)
      } catch(e) { alert("Test invocation failed. Check backend.") }
    },
    async testMonthlyJob() {
      try { 
        let res = await axios.post('http://127.0.0.1:5000/api/admin/test/monthly-report', {}, this.getHeaders())
        alert(res.data.msg)
      } catch(e) { alert("Test invocation failed. Check backend.") }
    }
  }
}
</script>
