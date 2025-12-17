from django.contrib import admin
from .models import Organization, Department, Position, Permission, PermissionGroup, PositionPermission, DepartmentPermission, Employee, EmployeePermissionGroup, ActivityLog


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name', 'parent', 'nip', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'short_name', 'nip', 'regon']
    ordering = ['name']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'parent', 'created_at']
    list_filter = ['organization', 'created_at']
    search_fields = ['name']
    ordering = ['organization', 'name']


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'department', 'created_at']
    list_filter = ['organization', 'department', 'created_at']
    search_fields = ['name']
    ordering = ['organization', 'name']


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'category']
    list_filter = ['category']
    search_fields = ['name']
    ordering = ['category', 'name']


@admin.register(PermissionGroup)
class PermissionGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    filter_horizontal = ['permissions']


@admin.register(PositionPermission)
class PositionPermissionAdmin(admin.ModelAdmin):
    list_display = ['position', 'permission_group', 'created_at']
    list_filter = ['permission_group']


@admin.register(DepartmentPermission)
class DepartmentPermissionAdmin(admin.ModelAdmin):
    list_display = ['department', 'permission_group', 'created_at']
    list_filter = ['permission_group']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'user', 'department', 'get_positions_display', 'is_active', 'created_at']
    list_filter = ['organization', 'department', 'is_active', 'created_at']
    search_fields = ['first_name', 'last_name', 'user__username']
    ordering = ['last_name', 'first_name']
    raw_id_fields = ['user']
    filter_horizontal = ['positions']


@admin.register(EmployeePermissionGroup)
class EmployeePermissionGroupAdmin(admin.ModelAdmin):
    list_display = ['employee', 'permission_group', 'created_at']
    list_filter = ['permission_group']


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'user', 'action', 'category', 'object_repr', 'ip_address']
    list_filter = ['action', 'category', 'created_at', 'user']
    search_fields = ['object_repr', 'description', 'user__username']
    readonly_fields = ['user', 'action', 'category', 'object_type', 'object_id', 'object_repr', 
                       'description', 'details', 'ip_address', 'user_agent', 'created_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
