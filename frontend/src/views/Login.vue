<template>
  <div class="row justify-content-center mt-5">
    <div class="col-md-5">
      <div class="card p-4">
        <h3 class="text-center mb-4 text-primary fw-bold">HMS</h3>
        <ul class="nav nav-pills nav-justified mb-4">
          <li class="nav-item">
            <a class="nav-link" :class="{active: !isRegister}" @click="isRegister = false" href="#">Login</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" :class="{active: isRegister}" @click="isRegister = true" href="#">Patient Register</a>
          </li>
        </ul>
        <form @submit.prevent="submitForm">
          <div class="mb-3">
            <label class="form-label">Username</label>
            <input type="text" class="form-control" v-model="form.username" required>
          </div>
          <div class="mb-3" v-if="isRegister">
            <label class="form-label">Email <small class="text-muted">(for appointment reminders)</small></label>
            <input type="email" class="form-control" v-model="form.email" required placeholder="your@gmail.com">
          </div>
          <div class="mb-3">
            <label class="form-label">Password</label>
            <input type="password" class="form-control" v-model="form.password" required>
          </div>
          <div class="d-grid">
            <button type="submit" class="btn btn-primary">{{ isRegister ? 'Register' : 'Login' }}</button>
          </div>
        </form>
        <div v-if="error" class="alert alert-danger mt-3">{{ error }}</div>
        <div v-if="success" class="alert alert-success mt-3">{{ success }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  data() {
    return {
      isRegister: false,
      form: { username: '', password: '', email: '' },
      error: '',
      success: ''
    }
  },
  methods: {
    async submitForm() {
      this.error = ''
      this.success = ''
      try {
        const config = { headers: { 'Content-Type': 'application/json' } }
        if (this.isRegister) {
          await axios.post('http://127.0.0.1:5000/api/register', this.form, config)
          this.success = 'Registration successful! Please login.'
          this.isRegister = false
          this.form.password = ''
        } else {
          const res = await axios.post('http://127.0.0.1:5000/api/login', this.form, config)
          localStorage.setItem('token', res.data.token)
          localStorage.setItem('role', res.data.role)
          localStorage.setItem('username', res.data.username)
          if (res.data.role === 'Admin') this.$router.push('/admin')
          else if (res.data.role === 'Doctor') this.$router.push('/doctor')
          else this.$router.push('/patient')
        }
      } catch (err) {
        this.error = err.response?.data?.msg || 'Error occurred'
      }
    }
  }
}
</script>
