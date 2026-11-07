import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import AdminDashboard from '../views/AdminDashboard.vue'
import DoctorDashboard from '../views/DoctorDashboard.vue'
import PatientDashboard from '../views/PatientDashboard.vue'

const routes = [
  { path: '/', component: Login },
  { path: '/admin', component: AdminDashboard, meta: { requiresAuth: true, role: 'Admin' } },
  { path: '/doctor', component: DoctorDashboard, meta: { requiresAuth: true, role: 'Doctor' } },
  { path: '/patient', component: PatientDashboard, meta: { requiresAuth: true, role: 'Patient' } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  const role = localStorage.getItem('role')
  if (to.meta.requiresAuth && !token) {
    return '/'
  } else if (to.meta.role && to.meta.role !== role) {
    return '/'
  } else {
    return true
  }
})

export default router
