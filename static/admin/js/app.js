/**
 * 管理后台主应用逻辑
 */

// ============================================
// 全局变量
// ============================================
let currentPage = 'users';
let currentUser = null;

// 分页状态 (使用 page 页码，从1开始)
const pagination = {
    users: { page: 1, page_size: 20, total: 0 },
    tasks: { page: 1, page_size: 20, total: 0 },
    results: { page: 1, page_size: 20, total: 0 },
};

// ============================================
// 工具函数
// ============================================

// 显示 Toast 消息
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = {
        success: 'fa-check-circle',
        error: 'fa-times-circle',
        warning: 'fa-exclamation-circle',
        info: 'fa-info-circle',
    }[type] || 'fa-info-circle';
    
    toast.innerHTML = `<i class="fas ${icon}"></i><span>${message}</span>`;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// 格式化日期时间
function formatDateTime(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
    });
}

// 显示模态框
function showModal(title, content) {
    const modal = document.getElementById('modal');
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = content;
    modal.classList.add('show');
}

// 关闭模态框
function closeModal() {
    document.getElementById('modal').classList.remove('show');
}

// 生成分页 HTML
function renderPagination(containerId, paginationState, loadFunction) {
    const container = document.getElementById(containerId);
    const totalPages = Math.ceil(paginationState.total / paginationState.page_size);
    const currentPageNum = paginationState.page;
    
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // 上一页
    html += `<button ${currentPageNum === 1 ? 'disabled' : ''} onclick="${loadFunction}(${currentPageNum - 1})">
        <i class="fas fa-chevron-left"></i>
    </button>`;
    
    // 页码
    const startPage = Math.max(1, currentPageNum - 2);
    const endPage = Math.min(totalPages, startPage + 4);
    for (let i = startPage; i <= endPage; i++) {
        html += `<button class="${i === currentPageNum ? 'active' : ''}" onclick="${loadFunction}(${i})">${i}</button>`;
    }
    
    // 下一页
    html += `<button ${currentPageNum === totalPages ? 'disabled' : ''} onclick="${loadFunction}(${currentPageNum + 1})">
        <i class="fas fa-chevron-right"></i>
    </button>`;
    
    container.innerHTML = html;
}

// ============================================
// 页面切换
// ============================================
function switchPage(pageName) {
    // 更新导航状态
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.page === pageName) {
            item.classList.add('active');
        }
    });
    
    // 更新页面显示
    document.querySelectorAll('.page-content').forEach(page => {
        page.classList.remove('active');
    });
    document.getElementById(`${pageName}-page`).classList.add('active');
    
    // 更新标题
    const titles = {
        users: '用户管理',
        tasks: '定时任务',
        schedules: '调度管理',
        results: '执行记录',
    };
    document.getElementById('page-title').textContent = titles[pageName] || pageName;
    
    currentPage = pageName;
    
    // 加载页面数据
    loadPageData(pageName);
}

// 加载页面数据
async function loadPageData(pageName) {
    switch (pageName) {
        case 'users':
            await loadUsers();
            break;
        case 'tasks':
            await loadTasks();
            break;
        case 'schedules':
            await loadSchedules();
            break;
        case 'results':
            await loadResults();
            break;
        case 'logs':
            await initializeLogFiles();
            break;
    }
}

// ============================================
// 用户管理
// ============================================
async function loadUsers(page = 1) {
    // 确保 page 至少为 1
    page = Math.max(1, page || 1);
    
    try {
        const search = document.getElementById('user-search').value;
        const isActive = document.getElementById('user-status-filter').value;
        
        const params = {
            page,
            page_size: pagination.users.page_size,
        };
        if (search) params.search = search;
        if (isActive !== '') params.is_active = isActive;
        
        const response = await UserAPI.list(params);
        const data = response.data || {};
        
        pagination.users.total = data.total || 0;
        pagination.users.page = page;
        
        renderUsersTable(data.items || []);
        renderPagination('users-pagination', pagination.users, 'loadUsers');
    } catch (error) {
        showToast('加载用户列表失败: ' + error.message, 'error');
    }
}

function renderUsersTable(users) {
    const tbody = document.getElementById('users-table-body');
    
    if (!users || users.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="empty-state">
                    <i class="fas fa-users"></i>
                    <p>暂无用户数据</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = users.map(user => `
        <tr>
            <td>${user.id}</td>
            <td>${user.username}</td>
            <td>${user.email}</td>
            <td>
                <span class="status-badge ${user.is_active ? 'active' : 'inactive'}">
                    ${user.is_active ? '激活' : '禁用'}
                </span>
            </td>
            <td>${user.is_superuser ? '<i class="fas fa-check text-success"></i>' : '<i class="fas fa-times text-muted"></i>'}</td>
            <td>${user.is_staff ? '<i class="fas fa-check text-success"></i>' : '<i class="fas fa-times text-muted"></i>'}</td>
            <td>${formatDateTime(user.created_at)}</td>
            <td class="action-btns">
                <button class="btn btn-sm btn-secondary" onclick="editUser(${user.id})" title="编辑">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteUser(${user.id})" title="删除">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

// 显示添加用户表单
function showAddUserForm() {
    const content = `
        <form id="add-user-form">
            <div class="form-row">
                <div class="form-group">
                    <label>用户名</label>
                    <input type="text" name="username" required minlength="3" maxlength="50">
                </div>
                <div class="form-group">
                    <label>邮箱</label>
                    <input type="email" name="email" required>
                </div>
            </div>
            <div class="form-group">
                <label>密码</label>
                <input type="password" name="password" required minlength="6">
            </div>
            <div class="form-row">
                <div class="form-group checkbox-group">
                    <input type="checkbox" name="is_active" id="user-is-active" checked>
                    <label for="user-is-active">激活状态</label>
                </div>
                <div class="form-group checkbox-group">
                    <input type="checkbox" name="is_staff" id="user-is-staff">
                    <label for="user-is-staff">管理员</label>
                </div>
                <div class="form-group checkbox-group">
                    <input type="checkbox" name="is_superuser" id="user-is-superuser">
                    <label for="user-is-superuser">超级管理员</label>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-outline" onclick="closeModal()">取消</button>
                <button type="submit" class="btn btn-primary">创建</button>
            </div>
        </form>
    `;
    showModal('添加用户', content);
    
    document.getElementById('add-user-form').onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const userData = {
            username: formData.get('username'),
            email: formData.get('email'),
            password: formData.get('password'),
            is_active: formData.has('is_active'),
            is_staff: formData.has('is_staff'),
            is_superuser: formData.has('is_superuser'),
        };
        
        try {
            await UserAPI.create(userData);
            showToast('用户创建成功', 'success');
            closeModal();
            loadUsers();
        } catch (error) {
            showToast('创建失败: ' + error.message, 'error');
        }
    };
}

// 编辑用户
async function editUser(userId) {
    try {
        const response = await UserAPI.get(userId);
        const user = response.data || {};
        const content = `
            <form id="edit-user-form">
                <div class="form-row">
                    <div class="form-group">
                        <label>用户名</label>
                        <input type="text" name="username" value="${user.username}" required minlength="3" maxlength="50">
                    </div>
                    <div class="form-group">
                        <label>邮箱</label>
                        <input type="email" name="email" value="${user.email}" required>
                    </div>
                </div>
                <div class="form-group">
                    <label>新密码 (留空则不修改)</label>
                    <input type="password" name="password" minlength="6">
                </div>
                <div class="form-row">
                    <div class="form-group checkbox-group">
                        <input type="checkbox" name="is_active" id="edit-user-is-active" ${user.is_active ? 'checked' : ''}>
                        <label for="edit-user-is-active">激活状态</label>
                    </div>
                    <div class="form-group checkbox-group">
                        <input type="checkbox" name="is_staff" id="edit-user-is-staff" ${user.is_staff ? 'checked' : ''}>
                        <label for="edit-user-is-staff">管理员</label>
                    </div>
                    <div class="form-group checkbox-group">
                        <input type="checkbox" name="is_superuser" id="edit-user-is-superuser" ${user.is_superuser ? 'checked' : ''}>
                        <label for="edit-user-is-superuser">超级管理员</label>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-outline" onclick="closeModal()">取消</button>
                    <button type="submit" class="btn btn-primary">保存</button>
                </div>
            </form>
        `;
        showModal('编辑用户', content);
        
        document.getElementById('edit-user-form').onsubmit = async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const userData = {
                username: formData.get('username'),
                email: formData.get('email'),
                is_active: formData.has('is_active'),
                is_staff: formData.has('is_staff'),
                is_superuser: formData.has('is_superuser'),
            };
            
            const password = formData.get('password');
            if (password) {
                userData.password = password;
            }
            
            try {
                await UserAPI.update(userId, userData);
                showToast('用户更新成功', 'success');
                closeModal();
                loadUsers();
            } catch (error) {
                showToast('更新失败: ' + error.message, 'error');
            }
        };
    } catch (error) {
        showToast('获取用户信息失败: ' + error.message, 'error');
    }
}

// 删除用户
async function deleteUser(userId) {
    if (!confirm('确定要删除该用户吗？此操作不可恢复。')) {
        return;
    }
    
    try {
        await UserAPI.delete(userId);
        showToast('用户删除成功', 'success');
        loadUsers();
    } catch (error) {
        showToast('删除失败: ' + error.message, 'error');
    }
}

// ============================================
// 定时任务管理
// ============================================
async function loadTasks(page = 1) {
    // 确保 page 至少为 1
    page = Math.max(1, page || 1);
    
    try {
        const enabled = document.getElementById('task-status-filter').value;
        
        const params = {
            page,
            page_size: pagination.tasks.page_size,
        };
        if (enabled !== '') params.enabled = enabled;
        
        const response = await TaskAPI.list(params);
        const data = response.data || {};
        
        pagination.tasks.total = data.total || 0;
        pagination.tasks.page = page;
        
        renderTasksTable(data.items || []);
        renderPagination('tasks-pagination', pagination.tasks, 'loadTasks');
    } catch (error) {
        showToast('加载任务列表失败: ' + error.message, 'error');
    }
}

function renderTasksTable(tasks) {
    const tbody = document.getElementById('tasks-table-body');
    
    if (!tasks || tasks.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="empty-state">
                    <i class="fas fa-clock"></i>
                    <p>暂无定时任务</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = tasks.map(task => `
        <tr>
            <td>${task.id}</td>
            <td>${task.name}</td>
            <td><code>${task.task}</code></td>
            <td>${task.interval_display || task.crontab_display || '-'}</td>
            <td>
                <label class="switch">
                    <input type="checkbox" ${task.enabled ? 'checked' : ''} onchange="toggleTask(${task.id}, ${task.enabled})">
                    <span class="slider"></span>
                </label>
            </td>
            <td>${task.total_run_count}</td>
            <td>${formatDateTime(task.last_run_at)}</td>
            <td class="action-btns">
                <button class="btn btn-sm btn-success" onclick="runTask(${task.id})" title="立即执行">
                    <i class="fas fa-play"></i>
                </button>
                <button class="btn btn-sm btn-secondary" onclick="editTask(${task.id})" title="编辑">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteTask(${task.id})" title="删除">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

// 显示添加任务表单
async function showAddTaskForm() {
    try {
        // 获取可用调度
        const [intervalsResp, crontabsResp] = await Promise.all([
            ScheduleAPI.intervals.list(),
            ScheduleAPI.crontabs.list(),
        ]);
        
        const intervals = intervalsResp.data || [];
        const crontabs = crontabsResp.data || [];
        
        const intervalOptions = intervals.map(i => `<option value="${i.id}">${i.display}</option>`).join('');
        const crontabOptions = crontabs.map(c => `<option value="${c.id}">${c.display}</option>`).join('');
        
        const content = `
            <form id="add-task-form">
                <div class="form-group">
                    <label><i class="fas fa-tag"></i> 任务名称</label>
                    <input type="text" name="name" required placeholder="请输入任务名称">
                </div>
                <div class="form-group">
                    <label><i class="fas fa-code"></i> 任务路径</label>
                    <input type="text" name="task" required placeholder="例如: celery_app.tasks.test_tasks.test_task">
                </div>
                <div class="form-group">
                    <label><i class="fas fa-clock"></i> 调度类型</label>
                    <div class="radio-group">
                        <label>
                            <input type="radio" name="schedule_type" value="interval" checked>
                            <span>间隔调度</span>
                        </label>
                        <label>
                            <input type="radio" name="schedule_type" value="crontab">
                            <span>Crontab调度</span>
                        </label>
                    </div>
                </div>
                <div id="interval-section" class="schedule-section active">
                    <div class="form-group">
                        <label>选择间隔</label>
                        <select name="interval_id">
                            <option value="">请选择间隔调度</option>
                            ${intervalOptions}
                        </select>
                    </div>
                </div>
                <div id="crontab-section" class="schedule-section disabled" style="display:none;">
                    <div class="form-group">
                        <label>选择Crontab</label>
                        <select name="crontab_id">
                            <option value="">请选择Crontab调度</option>
                            ${crontabOptions}
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label><i class="fas fa-list"></i> 任务参数 (JSON数组)</label>
                    <input type="text" name="args" placeholder="[]" value="[]">
                </div>
                <div class="form-group">
                    <label><i class="fas fa-cog"></i> 关键字参数 (JSON对象)</label>
                    <input type="text" name="kwargs" placeholder="{}" value="{}">
                </div>
                <div class="form-group">
                    <label><i class="fas fa-align-left"></i> 描述</label>
                    <textarea name="description" rows="2" placeholder="任务描述..."></textarea>
                </div>
                <div class="form-row">
                    <div class="form-group checkbox-group">
                        <input type="checkbox" name="enabled" id="task-enabled" checked>
                        <label for="task-enabled">启用</label>
                    </div>
                    <div class="form-group checkbox-group">
                        <input type="checkbox" name="one_off" id="task-one-off">
                        <label for="task-one-off">只执行一次</label>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-outline" onclick="closeModal()">取消</button>
                    <button type="submit" class="btn btn-primary"><i class="fas fa-plus"></i> 创建</button>
                </div>
            </form>
        `;
        showModal('添加定时任务', content);
        
        // 绑定调度类型切换事件
        bindScheduleTypeSwitch();
        
        document.getElementById('add-task-form').onsubmit = async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const scheduleType = formData.get('schedule_type');
            
            try {
                const taskData = {
                    name: formData.get('name'),
                    task: formData.get('task'),
                    args: JSON.parse(formData.get('args') || '[]'),
                    kwargs: JSON.parse(formData.get('kwargs') || '{}'),
                    description: formData.get('description'),
                    enabled: formData.has('enabled'),
                    one_off: formData.has('one_off'),
                };
                
                // 根据调度类型设置对应的ID
                if (scheduleType === 'interval') {
                    const intervalId = formData.get('interval_id');
                    if (intervalId) taskData.interval_id = parseInt(intervalId);
                    taskData.crontab_id = null;
                } else {
                    const crontabId = formData.get('crontab_id');
                    if (crontabId) taskData.crontab_id = parseInt(crontabId);
                    taskData.interval_id = null;
                }
                
                await TaskAPI.create(taskData);
                showToast('任务创建成功', 'success');
                closeModal();
                loadTasks();
            } catch (error) {
                showToast('创建失败: ' + error.message, 'error');
            }
        };
    } catch (error) {
        showToast('获取数据失败: ' + error.message, 'error');
    }
}

// 绑定调度类型切换事件
function bindScheduleTypeSwitch() {
    const radios = document.querySelectorAll('input[name="schedule_type"]');
    const intervalSection = document.getElementById('interval-section');
    const crontabSection = document.getElementById('crontab-section');
    
    radios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (e.target.value === 'interval') {
                intervalSection.style.display = 'block';
                intervalSection.classList.remove('disabled');
                intervalSection.classList.add('active');
                crontabSection.style.display = 'none';
                crontabSection.classList.add('disabled');
                crontabSection.classList.remove('active');
                // 清除crontab选择
                document.querySelector('select[name="crontab_id"]').value = '';
            } else {
                crontabSection.style.display = 'block';
                crontabSection.classList.remove('disabled');
                crontabSection.classList.add('active');
                intervalSection.style.display = 'none';
                intervalSection.classList.add('disabled');
                intervalSection.classList.remove('active');
                // 清除interval选择
                document.querySelector('select[name="interval_id"]').value = '';
            }
        });
    });
}

// 编辑任务
async function editTask(taskId) {
    try {
        const [taskResp, intervalsResp, crontabsResp] = await Promise.all([
            TaskAPI.get(taskId),
            ScheduleAPI.intervals.list(),
            ScheduleAPI.crontabs.list(),
        ]);
        
        const task = taskResp.data || {};
        const intervals = intervalsResp.data || [];
        const crontabs = crontabsResp.data || [];
        
        const intervalOptions = intervals.map(i => 
            `<option value="${i.id}" ${i.id === task.interval_id ? 'selected' : ''}>${i.display}</option>`
        ).join('');
        const crontabOptions = crontabs.map(c => 
            `<option value="${c.id}" ${c.id === task.crontab_id ? 'selected' : ''}>${c.display}</option>`
        ).join('');
        
        // 判断当前使用的调度类型
        const hasInterval = task.interval_id !== null && task.interval_id !== undefined;
        const hasCrontab = task.crontab_id !== null && task.crontab_id !== undefined;
        const scheduleType = hasCrontab ? 'crontab' : 'interval';
        
        // 处理 args 和 kwargs，确保正确显示
        const argsStr = typeof task.args === 'string' ? task.args : JSON.stringify(task.args || []);
        const kwargsStr = typeof task.kwargs === 'string' ? task.kwargs : JSON.stringify(task.kwargs || {});
        
        const content = `
            <form id="edit-task-form">
                <div class="form-group">
                    <label><i class="fas fa-tag"></i> 任务名称</label>
                    <input type="text" name="name" value="${task.name || ''}" required>
                </div>
                <div class="form-group">
                    <label><i class="fas fa-code"></i> 任务路径</label>
                    <input type="text" name="task" value="${task.task || ''}" required placeholder="例如: celery_app.tasks.test_tasks.test_task">
                </div>
                <div class="form-group">
                    <label><i class="fas fa-clock"></i> 调度类型</label>
                    <div class="radio-group">
                        <label>
                            <input type="radio" name="schedule_type" value="interval" ${scheduleType === 'interval' ? 'checked' : ''}>
                            <span>间隔调度</span>
                        </label>
                        <label>
                            <input type="radio" name="schedule_type" value="crontab" ${scheduleType === 'crontab' ? 'checked' : ''}>
                            <span>Crontab调度</span>
                        </label>
                    </div>
                </div>
                <div id="interval-section" class="schedule-section ${scheduleType === 'interval' ? 'active' : 'disabled'}" style="${scheduleType === 'crontab' ? 'display:none;' : ''}">
                    <div class="form-group">
                        <label>选择间隔</label>
                        <div class="schedule-select-row">
                            <select name="interval_id" id="edit-interval-select">
                                <option value="">请选择间隔调度</option>
                                ${intervalOptions}
                            </select>
                            <button type="button" class="btn btn-sm btn-secondary" onclick="editSelectedInterval()" title="编辑所选间隔">
                                <i class="fas fa-edit"></i>
                            </button>
                        </div>
                    </div>
                </div>
                <div id="crontab-section" class="schedule-section ${scheduleType === 'crontab' ? 'active' : 'disabled'}" style="${scheduleType === 'interval' ? 'display:none;' : ''}">
                    <div class="form-group">
                        <label>选择Crontab</label>
                        <div class="schedule-select-row">
                            <select name="crontab_id" id="edit-crontab-select">
                                <option value="">请选择Crontab调度</option>
                                ${crontabOptions}
                            </select>
                            <button type="button" class="btn btn-sm btn-secondary" onclick="editSelectedCrontab()" title="编辑所选Crontab">
                                <i class="fas fa-edit"></i>
                            </button>
                        </div>
                    </div>
                </div>
                <div class="form-group">
                    <label><i class="fas fa-list"></i> 任务参数 (JSON数组)</label>
                    <input type="text" name="args" value='${argsStr}'>
                </div>
                <div class="form-group">
                    <label><i class="fas fa-cog"></i> 关键字参数 (JSON对象)</label>
                    <input type="text" name="kwargs" value='${kwargsStr}'>
                </div>
                <div class="form-group">
                    <label><i class="fas fa-align-left"></i> 描述</label>
                    <textarea name="description" rows="2" placeholder="任务描述...">${task.description || ''}</textarea>
                </div>
                <div class="form-row">
                    <div class="form-group checkbox-group">
                        <input type="checkbox" name="enabled" id="edit-task-enabled" ${task.enabled ? 'checked' : ''}>
                        <label for="edit-task-enabled">启用</label>
                    </div>
                    <div class="form-group checkbox-group">
                        <input type="checkbox" name="one_off" id="edit-task-one-off" ${task.one_off ? 'checked' : ''}>
                        <label for="edit-task-one-off">只执行一次</label>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-outline" onclick="closeModal()">取消</button>
                    <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> 保存</button>
                </div>
            </form>
        `;
        showModal('编辑定时任务', content);
        
        // 绑定调度类型切换事件
        bindScheduleTypeSwitch();
        
        document.getElementById('edit-task-form').onsubmit = async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const currentScheduleType = formData.get('schedule_type');
            
            try {
                const taskData = {
                    name: formData.get('name'),
                    task: formData.get('task'),
                    args: JSON.parse(formData.get('args') || '[]'),
                    kwargs: JSON.parse(formData.get('kwargs') || '{}'),
                    description: formData.get('description'),
                    enabled: formData.has('enabled'),
                    one_off: formData.has('one_off'),
                };
                
                // 根据调度类型设置对应的ID，另一个设为null
                if (currentScheduleType === 'interval') {
                    const intervalId = formData.get('interval_id');
                    taskData.interval_id = intervalId ? parseInt(intervalId) : null;
                    taskData.crontab_id = null;
                } else {
                    const crontabId = formData.get('crontab_id');
                    taskData.crontab_id = crontabId ? parseInt(crontabId) : null;
                    taskData.interval_id = null;
                }
                
                await TaskAPI.update(taskId, taskData);
                showToast('任务更新成功', 'success');
                closeModal();
                loadTasks();
            } catch (error) {
                showToast('更新失败: ' + error.message, 'error');
            }
        };
    } catch (error) {
        showToast('获取任务信息失败: ' + error.message, 'error');
    }
}

// 在任务编辑中编辑所选间隔调度
async function editSelectedInterval() {
    const select = document.getElementById('edit-interval-select');
    if (!select || !select.value) {
        showToast('请先选择一个间隔调度', 'warning');
        return;
    }
    
    try {
        const intervalsResp = await ScheduleAPI.intervals.list();
        const intervals = intervalsResp.data || [];
        const interval = intervals.find(i => i.id === parseInt(select.value));
        
        if (!interval) {
            showToast('未找到所选间隔调度', 'error');
            return;
        }
        
        // 保存当前模态框内容
        const previousModalContent = document.querySelector('.modal-content').innerHTML;
        const previousModalTitle = document.querySelector('.modal-header h3').textContent;
        
        showEditIntervalForm(interval.id, interval.every, interval.period);
        
        // 修改表单提交后恢复上一个模态框
        const form = document.getElementById('edit-interval-form');
        const originalSubmit = form.onsubmit;
        form.onsubmit = async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            
            try {
                await ScheduleAPI.intervals.update(interval.id, {
                    every: parseInt(formData.get('every')),
                    period: formData.get('period'),
                });
                showToast('间隔调度更新成功', 'success');
                // 重新打开任务编辑
                closeModal();
                loadTasks();
                loadIntervals();
            } catch (error) {
                showToast('更新失败: ' + error.message, 'error');
            }
        };
    } catch (error) {
        showToast('加载间隔调度失败: ' + error.message, 'error');
    }
}

// 在任务编辑中编辑所选Crontab调度
async function editSelectedCrontab() {
    const select = document.getElementById('edit-crontab-select');
    if (!select || !select.value) {
        showToast('请先选择一个Crontab调度', 'warning');
        return;
    }
    
    try {
        const crontabsResp = await ScheduleAPI.crontabs.list();
        const crontabs = crontabsResp.data || [];
        const crontab = crontabs.find(c => c.id === parseInt(select.value));
        
        if (!crontab) {
            showToast('未找到所选Crontab调度', 'error');
            return;
        }
        
        showEditCrontabForm(crontab);
        
        // 修改表单提交后关闭模态框
        const form = document.getElementById('edit-crontab-form');
        form.onsubmit = async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            
            try {
                await ScheduleAPI.crontabs.update(crontab.id, {
                    minute: formData.get('minute'),
                    hour: formData.get('hour'),
                    day_of_week: formData.get('day_of_week'),
                    day_of_month: formData.get('day_of_month'),
                    month_of_year: formData.get('month_of_year'),
                    timezone: formData.get('timezone'),
                });
                showToast('Crontab调度更新成功', 'success');
                closeModal();
                loadTasks();
                loadCrontabs();
            } catch (error) {
                showToast('更新失败: ' + error.message, 'error');
            }
        };
    } catch (error) {
        showToast('加载Crontab调度失败: ' + error.message, 'error');
    }
}

// 切换任务状态
async function toggleTask(taskId, currentEnabled) {
    try {
        if (currentEnabled) {
            await TaskAPI.disable(taskId);
            showToast('任务已禁用', 'success');
        } else {
            await TaskAPI.enable(taskId);
            showToast('任务已启用', 'success');
        }
        loadTasks();
    } catch (error) {
        showToast('操作失败: ' + error.message, 'error');
    }
}

// 立即执行任务
async function runTask(taskId) {
    try {
        const result = await TaskAPI.runNow(taskId);
        showToast(result.message, 'success');
    } catch (error) {
        showToast('执行失败: ' + error.message, 'error');
    }
}

// 删除任务
async function deleteTask(taskId) {
    if (!confirm('确定要删除该任务吗？此操作不可恢复。')) {
        return;
    }
    
    try {
        await TaskAPI.delete(taskId);
        showToast('任务删除成功', 'success');
        loadTasks();
    } catch (error) {
        showToast('删除失败: ' + error.message, 'error');
    }
}

// ============================================
// 调度管理
// ============================================
async function loadSchedules() {
    await Promise.all([loadIntervals(), loadCrontabs()]);
}

async function loadIntervals() {
    try {
        const response = await ScheduleAPI.intervals.list();
        renderIntervalsTable(response.data || []);
    } catch (error) {
        showToast('加载间隔调度失败: ' + error.message, 'error');
    }
}

function renderIntervalsTable(intervals) {
    const tbody = document.getElementById('intervals-table-body');
    
    if (!intervals || intervals.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="empty-state">
                    <i class="fas fa-clock"></i>
                    <p>暂无间隔调度</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = intervals.map(interval => `
        <tr>
            <td>${interval.id}</td>
            <td>${interval.every}</td>
            <td>${interval.period}</td>
            <td>${interval.display}</td>
            <td class="action-btns">
                <button class="btn btn-sm btn-primary" onclick="showEditIntervalForm(${interval.id}, ${interval.every}, '${interval.period}')" title="编辑">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteInterval(${interval.id})" title="删除">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function showAddIntervalForm() {
    const content = `
        <form id="add-interval-form">
            <div class="form-row">
                <div class="form-group">
                    <label>间隔数量</label>
                    <input type="number" name="every" min="1" required>
                </div>
                <div class="form-group">
                    <label>间隔类型</label>
                    <select name="period" required>
                        <option value="seconds">秒 (seconds)</option>
                        <option value="minutes">分钟 (minutes)</option>
                        <option value="hours">小时 (hours)</option>
                        <option value="days">天 (days)</option>
                    </select>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-outline" onclick="closeModal()">取消</button>
                <button type="submit" class="btn btn-primary">创建</button>
            </div>
        </form>
    `;
    showModal('添加间隔调度', content);
    
    document.getElementById('add-interval-form').onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        
        try {
            await ScheduleAPI.intervals.create({
                every: parseInt(formData.get('every')),
                period: formData.get('period'),
            });
            showToast('间隔调度创建成功', 'success');
            closeModal();
            loadIntervals();
        } catch (error) {
            showToast('创建失败: ' + error.message, 'error');
        }
    };
}

function showEditIntervalForm(intervalId, every, period) {
    const content = `
        <form id="edit-interval-form">
            <div class="form-row">
                <div class="form-group">
                    <label>间隔数量</label>
                    <input type="number" name="every" min="1" value="${every}" required>
                </div>
                <div class="form-group">
                    <label>间隔类型</label>
                    <select name="period" required>
                        <option value="seconds" ${period === 'seconds' ? 'selected' : ''}>秒 (seconds)</option>
                        <option value="minutes" ${period === 'minutes' ? 'selected' : ''}>分钟 (minutes)</option>
                        <option value="hours" ${period === 'hours' ? 'selected' : ''}>小时 (hours)</option>
                        <option value="days" ${period === 'days' ? 'selected' : ''}>天 (days)</option>
                    </select>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-outline" onclick="closeModal()">取消</button>
                <button type="submit" class="btn btn-primary">保存</button>
            </div>
        </form>
    `;
    showModal('编辑间隔调度', content);
    
    document.getElementById('edit-interval-form').onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        
        try {
            await ScheduleAPI.intervals.update(intervalId, {
                every: parseInt(formData.get('every')),
                period: formData.get('period'),
            });
            showToast('间隔调度更新成功', 'success');
            closeModal();
            loadIntervals();
            loadTasks();
        } catch (error) {
            showToast('更新失败: ' + error.message, 'error');
        }
    };
}

async function deleteInterval(intervalId) {
    if (!confirm('确定要删除该间隔调度吗？')) {
        return;
    }
    
    try {
        await ScheduleAPI.intervals.delete(intervalId);
        showToast('间隔调度删除成功', 'success');
        loadIntervals();
    } catch (error) {
        showToast('删除失败: ' + error.message, 'error');
    }
}

async function loadCrontabs() {
    try {
        const response = await ScheduleAPI.crontabs.list();
        renderCrontabsTable(response.data || []);
    } catch (error) {
        showToast('加载Crontab调度失败: ' + error.message, 'error');
    }
}

function renderCrontabsTable(crontabs) {
    const tbody = document.getElementById('crontabs-table-body');
    
    if (!crontabs || crontabs.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="empty-state">
                    <i class="fas fa-calendar-alt"></i>
                    <p>暂无Crontab调度</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = crontabs.map(crontab => `
        <tr>
            <td>${crontab.id}</td>
            <td>${crontab.minute}</td>
            <td>${crontab.hour}</td>
            <td>${crontab.day_of_week}</td>
            <td>${crontab.day_of_month}</td>
            <td>${crontab.month_of_year}</td>
            <td>${crontab.timezone}</td>
            <td class="action-btns">
                <button class="btn btn-sm btn-primary" onclick='showEditCrontabForm(${JSON.stringify(crontab)})' title="编辑">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteCrontab(${crontab.id})" title="删除">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function showAddCrontabForm() {
    const content = `
        <form id="add-crontab-form">
            <div class="form-row">
                <div class="form-group">
                    <label>分钟 (0-59)</label>
                    <input type="text" name="minute" value="*" required>
                </div>
                <div class="form-group">
                    <label>小时 (0-23)</label>
                    <input type="text" name="hour" value="*" required>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>星期几 (0-6)</label>
                    <input type="text" name="day_of_week" value="*" required>
                </div>
                <div class="form-group">
                    <label>日期 (1-31)</label>
                    <input type="text" name="day_of_month" value="*" required>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>月份 (1-12)</label>
                    <input type="text" name="month_of_year" value="*" required>
                </div>
                <div class="form-group">
                    <label>时区</label>
                    <input type="text" name="timezone" value="Asia/Shanghai" required>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-outline" onclick="closeModal()">取消</button>
                <button type="submit" class="btn btn-primary">创建</button>
            </div>
        </form>
    `;
    showModal('添加Crontab调度', content);
    
    document.getElementById('add-crontab-form').onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        
        try {
            await ScheduleAPI.crontabs.create({
                minute: formData.get('minute'),
                hour: formData.get('hour'),
                day_of_week: formData.get('day_of_week'),
                day_of_month: formData.get('day_of_month'),
                month_of_year: formData.get('month_of_year'),
                timezone: formData.get('timezone'),
            });
            showToast('Crontab调度创建成功', 'success');
            closeModal();
            loadCrontabs();
        } catch (error) {
            showToast('创建失败: ' + error.message, 'error');
        }
    };
}

function showEditCrontabForm(crontab) {
    const content = `
        <form id="edit-crontab-form">
            <div class="form-row">
                <div class="form-group">
                    <label>分钟 (0-59)</label>
                    <input type="text" name="minute" value="${crontab.minute}" required>
                </div>
                <div class="form-group">
                    <label>小时 (0-23)</label>
                    <input type="text" name="hour" value="${crontab.hour}" required>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>星期几 (0-6)</label>
                    <input type="text" name="day_of_week" value="${crontab.day_of_week}" required>
                </div>
                <div class="form-group">
                    <label>日期 (1-31)</label>
                    <input type="text" name="day_of_month" value="${crontab.day_of_month}" required>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>月份 (1-12)</label>
                    <input type="text" name="month_of_year" value="${crontab.month_of_year}" required>
                </div>
                <div class="form-group">
                    <label>时区</label>
                    <input type="text" name="timezone" value="${crontab.timezone}" required>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-outline" onclick="closeModal()">取消</button>
                <button type="submit" class="btn btn-primary">保存</button>
            </div>
        </form>
    `;
    showModal('编辑Crontab调度', content);
    
    document.getElementById('edit-crontab-form').onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        
        try {
            await ScheduleAPI.crontabs.update(crontab.id, {
                minute: formData.get('minute'),
                hour: formData.get('hour'),
                day_of_week: formData.get('day_of_week'),
                day_of_month: formData.get('day_of_month'),
                month_of_year: formData.get('month_of_year'),
                timezone: formData.get('timezone'),
            });
            showToast('Crontab调度更新成功', 'success');
            closeModal();
            loadCrontabs();
            loadTasks();
        } catch (error) {
            showToast('更新失败: ' + error.message, 'error');
        }
    };
}

async function deleteCrontab(crontabId) {
    if (!confirm('确定要删除该Crontab调度吗？')) {
        return;
    }
    
    try {
        await ScheduleAPI.crontabs.delete(crontabId);
        showToast('Crontab调度删除成功', 'success');
        loadCrontabs();
    } catch (error) {
        showToast('删除失败: ' + error.message, 'error');
    }
}

// ============================================
// 执行记录管理
// ============================================
async function loadResults(page = 1) {
    // 确保 page 至少为 1
    page = Math.max(1, page || 1);
    
    try {
        const taskName = document.getElementById('result-task-name').value;
        const status = document.getElementById('result-status-filter').value;
        
        const params = {
            page,
            page_size: pagination.results.page_size,
        };
        if (taskName) params.task_name = taskName;
        if (status) params.status = status;
        
        const response = await ResultAPI.list(params);
        const data = response.data || {};
        
        pagination.results.total = data.total || 0;
        pagination.results.page = page;
        
        renderResultsTable(data.items || []);
        renderPagination('results-pagination', pagination.results, 'loadResults');
    } catch (error) {
        showToast('加载执行记录失败: ' + error.message, 'error');
    }
}

function renderResultsTable(results) {
    const tbody = document.getElementById('results-table-body');
    
    if (!results || results.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="empty-state">
                    <i class="fas fa-list-alt"></i>
                    <p>暂无执行记录</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = results.map(result => `
        <tr>
            <td><code>${result.task_id.substring(0, 8)}...</code></td>
            <td>${result.task_name || '-'}</td>
            <td>
                <span class="status-badge ${result.status.toLowerCase()}">
                    ${result.status}
                </span>
            </td>
            <td>${result.worker || '-'}</td>
            <td>${formatDateTime(result.date_created)}</td>
            <td>${formatDateTime(result.date_done)}</td>
            <td class="action-btns">
                <button class="btn btn-sm btn-secondary" onclick="viewResult('${result.task_id}')" title="查看详情">
                    <i class="fas fa-eye"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

async function viewResult(taskId) {
    try {
        const response = await ResultAPI.get(taskId);
        const result = response.data || {};
        const content = `
            <div class="result-detail">
                <div class="form-group">
                    <label>任务ID</label>
                    <p><code>${result.task_id}</code></p>
                </div>
                <div class="form-group">
                    <label>任务名称</label>
                    <p>${result.task_name || '-'}</p>
                </div>
                <div class="form-group">
                    <label>状态</label>
                    <p><span class="status-badge ${result.status.toLowerCase()}">${result.status}</span></p>
                </div>
                <div class="form-group">
                    <label>参数</label>
                    <p><code>${result.task_args || '[]'}</code></p>
                </div>
                <div class="form-group">
                    <label>关键字参数</label>
                    <p><code>${result.task_kwargs || '{}'}</code></p>
                </div>
                <div class="form-group">
                    <label>结果</label>
                    <p><code>${result.result || '-'}</code></p>
                </div>
                ${result.traceback ? `
                <div class="form-group">
                    <label>错误信息</label>
                    <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; overflow: auto; max-height: 200px;">${result.traceback}</pre>
                </div>
                ` : ''}
                <div class="form-row">
                    <div class="form-group">
                        <label>创建时间</label>
                        <p>${formatDateTime(result.date_created)}</p>
                    </div>
                    <div class="form-group">
                        <label>完成时间</label>
                        <p>${formatDateTime(result.date_done)}</p>
                    </div>
                </div>
            </div>
        `;
        showModal('执行详情', content);
    } catch (error) {
        showToast('获取详情失败: ' + error.message, 'error');
    }
}

async function cleanupResults() {
    const days = prompt('保留最近多少天的记录？（默认30天）', '30');
    if (days === null) return;
    
    try {
        const result = await ResultAPI.cleanup(parseInt(days) || 30);
        showToast(result.message, 'success');
        loadResults();
    } catch (error) {
        showToast('清理失败: ' + error.message, 'error');
    }
}

// ============================================
// 登录相关
// ============================================
async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('login-error');
    
    try {
        const data = await AuthAPI.login(username, password);
        
        // 处理新的响应格式 { code, message, data: { access_token, ... } }
        let token;
        if (data.data && data.data.access_token) {
            token = data.data.access_token;
        } else if (data.access_token) {
            token = data.access_token;
        } else {
            throw new Error('登录失败：没有获得有效的 token');
        }
        
        api.setToken(token);
        
        // 显示管理界面
        document.getElementById('login-page').style.display = 'none';
        document.getElementById('admin-page').style.display = 'flex';
        document.getElementById('current-user').textContent = username;
        
        // 加载仪表板数据
        loadDashboard();
    } catch (error) {
        errorDiv.textContent = error.message;
        errorDiv.style.display = 'block';
    }
}

function handleLogout() {
    api.clearToken();
    document.getElementById('admin-page').style.display = 'none';
    document.getElementById('login-page').style.display = 'flex';
    document.getElementById('username').value = '';
    document.getElementById('password').value = '';
    document.getElementById('login-error').style.display = 'none';
}

// 检查登录状态
function checkAuth() {
    const token = localStorage.getItem('access_token');
    if (token) {
        api.setToken(token);
        document.getElementById('login-page').style.display = 'none';
        document.getElementById('admin-page').style.display = 'flex';
        loadUsers();
    }
}

// ============================================
// 初始化
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    // 检查登录状态
    checkAuth();
    
    // 登录表单提交
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    
    // 退出登录
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    
    // 侧边栏导航
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            switchPage(item.dataset.page);
        });
    });
    
    // 侧边栏切换（移动端）
    document.getElementById('sidebar-toggle').addEventListener('click', () => {
        document.querySelector('.sidebar').classList.toggle('show');
    });
    
    // 模态框关闭（只允许点击关闭按钮）
    document.querySelector('.modal-close').addEventListener('click', closeModal);
    
    // 用户管理按钮
    document.getElementById('add-user-btn').addEventListener('click', showAddUserForm);
    document.getElementById('user-search-btn').addEventListener('click', () => loadUsers(0));
    
    // 任务管理按钮
    document.getElementById('add-task-btn').addEventListener('click', showAddTaskForm);
    document.getElementById('task-search-btn').addEventListener('click', () => loadTasks(1));
    
    // 调度管理选项卡
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(`${btn.dataset.tab}-tab`).classList.add('active');
        });
    });
    
    // 调度管理按钮
    document.getElementById('add-interval-btn').addEventListener('click', showAddIntervalForm);
    document.getElementById('add-crontab-btn').addEventListener('click', showAddCrontabForm);
    
    // 执行记录按钮
    document.getElementById('result-search-btn').addEventListener('click', () => loadResults(0));
    document.getElementById('cleanup-results-btn').addEventListener('click', cleanupResults);
    
    // 日志查询相关事件
    document.getElementById('log-query-btn').addEventListener('click', executeLogQuery);
    document.getElementById('log-clear-btn').addEventListener('click', clearLogQuery);
    
    // 查询示例按钮事件
    document.querySelectorAll('.example-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.getElementById('jq-filter').value = btn.dataset.filter;
        });
    });
    
    // 日志详情模态框关闭按钮
    document.querySelector('#log-detail-modal .modal-close').addEventListener('click', () => {
        document.getElementById('log-detail-modal').classList.remove('show');
    });
});

// ============================================
// 日志查询功能
// ============================================

// 初始化日志文件列表
let logFilesInitialized = false;
async function initializeLogFiles() {
    try {
        const result = await api.get('/admin/logs/files');
        
        if (!result.data || result.data.length === 0) {
            showToast('没有可用的日志文件', 'info');
            return;
        }
        
        const select = document.getElementById('log-file-select');
        
        // 清空并重新填充选项
        select.innerHTML = '<option value="">-- 选择日志文件 --</option>';
        result.data.forEach(file => {
            const option = document.createElement('option');
            option.value = file;
            option.textContent = file;
            select.appendChild(option);
        });
        
        // 只绑定一次 change 事件，避免重复绑定
        if (!logFilesInitialized) {
            select.addEventListener('change', onLogFileSelectChange);
            logFilesInitialized = true;
        }
    } catch (error) {
        console.error('加载日志文件列表失败:', error);
        // 不显示 toast，避免在权限不足时反复提示
        // 只在控制台记录错误
        const resultsDiv = document.getElementById('log-results');
        if (resultsDiv) {
            resultsDiv.innerHTML = '<p class="no-data">加载失败: ' + error.message + '</p>';
        }
    }
}

// 日志文件选择改变事件
async function onLogFileSelectChange() {
    // 当用户手动改变选择时，可以在这里添加逻辑
    // 例如自动刷新日志文件列表（如果需要）
    // 目前暂时不做任何操作
}

async function executeLogQuery() {
    const filename = document.getElementById('log-file-select').value;
    const jqFilter = document.getElementById('jq-filter').value || '.';
    
    console.log('[executeLogQuery] filename:', filename, 'jqFilter:', jqFilter);
    
    if (!filename) {
        showToast('请选择日志文件', 'warning');
        return;
    }
    
    try {
        const resultsDiv = document.getElementById('log-results');
        resultsDiv.innerHTML = '<p class="no-data"><i class="fas fa-spinner fa-spin"></i> 查询中...</p>';
        
        // 使用 ApiClient POST 请求，参数放在请求体中
        console.log('[executeLogQuery] 发送请求:', {filename, jq_filter: jqFilter});
        const result = await api.post('/admin/logs/query', {
            filename: filename,
            jq_filter: jqFilter
        });
        console.log('[executeLogQuery] 收到响应:', result);
        
        // 检查响应状态（使用自定义 code）
        if (!isSuccess(result.code)) {
            showToast('查询失败: ' + result.message, 'error');
            resultsDiv.innerHTML = `<p class="no-data">查询失败: ${result.message}</p>`;
            return;
        }
        
        const data = result.data;
        if (!data.results || data.results.length === 0) {
            resultsDiv.innerHTML = '<p class="no-data">没有匹配的记录</p>';
            return;
        }
        
        let html = `<p style="color: var(--text-secondary); margin-bottom: 15px;">找到 <strong>${data.count}</strong> 条记录</p>`;
        
        data.results.forEach((record, index) => {
            if (typeof record === 'object') {
                html += renderLogEntry(record, index);
            } else {
                html += `<div class="log-entry"><pre>${JSON.stringify(record, null, 2)}</pre></div>`;
            }
        });
        
        resultsDiv.innerHTML = html;
        
        // 为所有详情按钮添加事件监听
        document.querySelectorAll('.log-detail-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const record = JSON.parse(btn.dataset.record);
                showLogDetail(record);
            });
        });
        
        showToast('查询成功', 'success');
    } catch (error) {
        showToast('查询出错: ' + error.message, 'error');
        document.getElementById('log-results').innerHTML = `<p class="no-data">出错: ${error.message}</p>`;
    }
}

function renderLogEntry(record, index) {
    const cells = [];
    for (const [key, value] of Object.entries(record)) {
        let valueHtml = value;
        let className = 'string';
        
        if (typeof value === 'number') {
            className = 'number';
            valueHtml = value.toString();
        } else if (typeof value === 'boolean') {
            className = 'boolean';
            valueHtml = value ? '是' : '否';
        } else if (typeof value === 'string') {
            className = 'string';
            // 截断长字符串
            if (value.length > 100) {
                valueHtml = value.substring(0, 100) + '...';
            }
        } else {
            valueHtml = JSON.stringify(value);
            if (valueHtml.length > 100) {
                valueHtml = valueHtml.substring(0, 100) + '...';
            }
        }
        
        cells.push(`
            <div class="log-entry-cell">
                <div class="log-entry-cell-label">${key}</div>
                <div class="log-entry-cell-value ${className}">${valueHtml}</div>
            </div>
        `);
    }
    
    const recordStr = JSON.stringify(record).replace(/"/g, '&quot;');
    return `
        <div class="log-entry">
            <div class="log-entry-grid">
                ${cells.join('')}
            </div>
            <div class="log-entry-footer">
                <button class="btn btn-primary log-detail-btn" data-record="${recordStr}">
                    <i class="fas fa-expand"></i>
                    查看详情
                </button>
            </div>
        </div>
    `;
}

function showLogDetail(record) {
    const modal = document.getElementById('log-detail-modal');
    const content = document.getElementById('log-detail-content');
    content.textContent = JSON.stringify(record, null, 2);
    modal.classList.add('show');
}

function clearLogQuery() {
    document.getElementById('jq-filter').value = '.';
    document.getElementById('log-results').innerHTML = '<p class="no-data">请选择日志文件并执行查询</p>';
}

// 关闭日志详情模态框
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-close')) {
        e.target.closest('.modal').classList.remove('show');
    }
});

