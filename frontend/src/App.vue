<template>
  <div>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary shadow-sm" v-if="isLoggedIn">
      <div class="container">
        <a class="navbar-brand fw-bold" href="#">HMS</a>
        <div class="d-flex">
          <button class="btn btn-light btn-sm" @click="logout">Logout ({{ username }})</button>
        </div>
      </div>
    </nav>
    <div class="container mt-4">
      <router-view></router-view>
    </div>
  </div>
</template>

<script>
export default {
  computed: {
    isLoggedIn() {
      return this.$route.path !== '/'
    },
    username() {
      return localStorage.getItem('username') || 'User'
    }
  },
  methods: {
    logout() {
      localStorage.clear()
      window.location.href = '/'
    }
  }
}
</script>

<style>
body {
  background-color: #f8f9fa;
  font-family: 'Inter', sans-serif;
}
.card {
  border-radius: 10px;
  border: none;
  box-shadow: 0 4px 6px rgba(0,0,0,0.05);
}
.btn {
  border-radius: 6px;
}
</style>
