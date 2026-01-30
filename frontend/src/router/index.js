import { createRouter, createWebHistory } from 'vue-router'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

NProgress.configure({ showSpinner: false })

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { title: '登录', requireAuth: false },
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/views/layout/index.vue'),
    redirect: '/dashboard',
    meta: { requireAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '工作台' },
      },
      // System Management
      {
        path: 'system/users',
        name: 'Users',
        component: () => import('@/views/system/users/index.vue'),
        meta: { title: '用户管理' },
      },
      {
        path: 'system/roles',
        name: 'Roles',
        component: () => import('@/views/system/roles/index.vue'),
        meta: { title: '角色管理' },
      },
      // Scheduler
      {
        path: 'scheduler/jobs',
        name: 'Jobs',
        component: () => import('@/views/scheduler/jobs/index.vue'),
        meta: { title: '任务管理' },
      },
      {
        path: 'scheduler/flows',
        name: 'JobFlows',
        component: () => import('@/views/scheduler/flows/index.vue'),
        meta: { title: '工作流管理' },
      },
      // Reports
      {
        path: 'report/list',
        name: 'Reports',
        component: () => import('@/views/report/list/index.vue'),
        meta: { title: '报表管理' },
      },
      {
        path: 'report/datasources',
        name: 'DataSources',
        component: () => import('@/views/report/datasources/index.vue'),
        meta: { title: '数据源管理' },
      },
      // Config
      {
        path: 'config/tables',
        name: 'ConfigTables',
        component: () => import('@/views/config/tables/index.vue'),
        meta: { title: '配置管理' },
      },
      // Workflow
      {
        path: 'workflow/definitions',
        name: 'WorkflowDefinitions',
        component: () => import('@/views/workflow/definitions/index.vue'),
        meta: { title: '流程管理' },
      },
      {
        path: 'workflow/todo',
        name: 'WorkflowTodo',
        component: () => import('@/views/workflow/todo/index.vue'),
        meta: { title: '待办事项' },
      },
      // Audit
      {
        path: 'audit/logs',
        name: 'AuditLogs',
        component: () => import('@/views/audit/logs/index.vue'),
        meta: { title: '操作日志' },
      },
      // Messages
      {
        path: 'message/templates',
        name: 'MessageTemplates',
        component: () => import('@/views/message/templates/index.vue'),
        meta: { title: '消息模板' },
      },
      {
        path: 'notifications',
        name: 'Notifications',
        component: () => import('@/views/notifications/index.vue'),
        meta: { title: '站内消息' },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/404.vue'),
    meta: { title: '404' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  NProgress.start()
  document.title = to.meta.title ? `${to.meta.title} - OPS` : 'OPS'

  const token = localStorage.getItem('token')
  if (to.meta.requireAuth !== false && !token) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

router.afterEach(() => {
  NProgress.done()
})

export default router
