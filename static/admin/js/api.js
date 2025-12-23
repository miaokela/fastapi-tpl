/**
 * API 配置和请求封装
 * 响应格式: { code: number, message: string, data: any }
 * code: 1xxx 成功, 4xxx 客户端错误, 5xxx 服务端错误
 */

const API_BASE_URL = '/api/v1';

// 响应码常量
const ResponseCode = {
    SUCCESS: 1000,
    CREATED: 1001,
    UPDATED: 1002,
    DELETED: 1003,
    BAD_REQUEST: 4000,
    UNAUTHORIZED: 4010,
    FORBIDDEN: 4030,
    NOT_FOUND: 4040,
};

// 判断响应是否成功
function isSuccess(code) {
    return code >= 1000 && code < 2000;
}

// API 请求工具类
class ApiClient {
    constructor() {
        this.baseUrl = API_BASE_URL;
        this.isReloading = false; // 防止无限刷新的标志
    }

    // 获取 Token（每次从 localStorage 读取最新值）
    getToken() {
        return localStorage.getItem('access_token');
    }

    // 设置 Token
    setToken(token) {
        localStorage.setItem('access_token', token);
        console.log('✅ Token 已设置:', token.substring(0, 20) + '...');
    }

    // 清除 Token
    clearToken() {
        localStorage.removeItem('access_token');
        console.log('✅ Token 已清除');
    }

    // 获取请求头
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
        };
        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        return headers;
    }

    // 通用请求方法
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            ...options,
            headers: {
                ...this.getHeaders(),
                ...options.headers,
            },
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            // 新响应格式：通过 code 判断
            if (data.code !== undefined) {
                // 处理未授权和权限错误
                if (data.code === ResponseCode.UNAUTHORIZED || data.code === 4011 || data.code === 4012) {
                    console.log('❌ 认证错误 (401)，清除 token 并重新加载页面');
                    this.clearToken();
                    if (!this.isReloading) {
                        this.isReloading = true;
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000);
                    }
                    throw new Error(data.message || '请先登录');
                }
                
                // 403 权限不足，如果有 token 说明是真的权限不足，否则可能是 token 没传
                if (data.code === ResponseCode.FORBIDDEN) {
                    const token = this.getToken();
                    if (!token) {
                        console.log('❌ 权限错误但没有 token，可能是认证问题');
                        this.clearToken();
                        if (!this.isReloading) {
                            this.isReloading = true;
                            setTimeout(() => {
                                window.location.reload();
                            }, 1000);
                        }
                    }
                    throw new Error(data.message || '权限不足');
                }
                
                // 处理其他错误
                if (!isSuccess(data.code)) {
                    throw new Error(data.message || '请求失败');
                }
                
                return data;
            }if (!this.isReloading) {
                        this.isReloading = true;
                        window.location.reload();
                    }
            
            // 兼容旧格式（如登录接口）
            if (!response.ok) {
                if (response.status === 401) {
                    this.clearToken();
                    window.location.reload();
                }
                throw new Error(data.detail || data.message || '请求失败');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // GET 请求
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    }

    // POST 请求
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    // PUT 请求
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    // DELETE 请求
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
}

// 创建 API 客户端实例
const api = new ApiClient();

// ============================================
// 认证 API
// ============================================
const AuthAPI = {
    // 登录
    async login(username, password) {
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });
        
        const data = await response.json();
        
        // 新的响应格式：code 不为空时检查 code
        if (data.code !== undefined) {
            if (!isSuccess(data.code)) {
                throw new Error(data.message || '登录失败');
            }
            return data;
        }
        
        // 兼容旧格式
        if (!response.ok) {
            throw new Error(data.detail || '登录失败');
        }
        
        return data;
    },

    // 获取当前用户信息
    async getCurrentUser() {
        const response = await fetch('/auth/me', {
            method: 'GET',
            headers: api.getHeaders(),
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || '获取用户信息失败');
        }
        
        return data;
    },
};

// ============================================
// 用户管理 API
// ============================================
const UserAPI = {
    // 获取用户列表
    async list(params = {}) {
        return api.get('/admin/users', params);
    },

    // 获取用户详情
    async get(userId) {
        return api.get(`/admin/users/${userId}`);
    },

    // 创建用户
    async create(userData) {
        return api.post('/admin/users', userData);
    },

    // 更新用户
    async update(userId, userData) {
        return api.put(`/admin/users/${userId}`, userData);
    },

    // 删除用户
    async delete(userId) {
        return api.delete(`/admin/users/${userId}`);
    },
};

// ============================================
// 定时任务 API
// ============================================
const TaskAPI = {
    // 获取任务列表
    async list(params = {}) {
        return api.get('/admin/tasks', params);
    },

    // 获取任务详情
    async get(taskId) {
        return api.get(`/admin/tasks/${taskId}`);
    },

    // 创建任务
    async create(taskData) {
        return api.post('/admin/tasks', taskData);
    },

    // 更新任务
    async update(taskId, taskData) {
        return api.put(`/admin/tasks/${taskId}`, taskData);
    },

    // 删除任务
    async delete(taskId) {
        return api.delete(`/admin/tasks/${taskId}`);
    },

    // 启用任务
    async enable(taskId) {
        return api.post(`/admin/tasks/${taskId}/enable`);
    },

    // 禁用任务
    async disable(taskId) {
        return api.post(`/admin/tasks/${taskId}/disable`);
    },

    // 立即执行任务
    async runNow(taskId) {
        return api.post(`/admin/tasks/${taskId}/run`);
    },

    // 获取可用任务列表
    async getAvailable() {
        return api.get('/admin/available-tasks');
    },
};

// ============================================
// 调度 API
// ============================================
const ScheduleAPI = {
    // 间隔调度
    intervals: {
        async list() {
            return api.get('/admin/schedules/intervals');
        },
        async create(data) {
            return api.post('/admin/schedules/intervals', data);
        },
        async update(intervalId, data) {
            return api.put(`/admin/schedules/intervals/${intervalId}`, data);
        },
        async delete(intervalId) {
            return api.delete(`/admin/schedules/intervals/${intervalId}`);
        },
    },

    // Crontab 调度
    crontabs: {
        async list() {
            return api.get('/admin/schedules/crontabs');
        },
        async create(data) {
            return api.post('/admin/schedules/crontabs', data);
        },
        async update(crontabId, data) {
            return api.put(`/admin/schedules/crontabs/${crontabId}`, data);
        },
        async delete(crontabId) {
            return api.delete(`/admin/schedules/crontabs/${crontabId}`);
        },
    },
};

// ============================================
// 任务结果 API
// ============================================
const ResultAPI = {
    // 获取结果列表
    async list(params = {}) {
        return api.get('/admin/results', params);
    },

    // 获取结果详情
    async get(taskId) {
        return api.get(`/admin/results/${taskId}`);
    },

    // 清理旧记录
    async cleanup(days = 30) {
        return api.delete(`/admin/results/cleanup?days=${days}`);
    },
};

// ============================================
// 统计 API
// ============================================
const StatisticsAPI = {
    async get() {
        return api.get('/admin/statistics');
    },
};
