// 当前登录用户（内部系统：选择员工即登录，持久化到 localStorage）
import { ref } from 'vue'
import type { Employee } from '../api/types'

const KEY = 'erp_current_user'

function load(): Employee | null {
  try {
    const raw = localStorage.getItem(KEY)
    return raw ? (JSON.parse(raw) as Employee) : null
  } catch {
    return null
  }
}

const currentUser = ref<Employee | null>(load())

export function useCurrentUser() {
  function setUser(u: Employee | null) {
    currentUser.value = u
    if (u) localStorage.setItem(KEY, JSON.stringify(u))
    else localStorage.removeItem(KEY)
  }
  return { currentUser, setUser }
}
