from django.contrib import admin
from .models import AuctionListing, Bid, Comment, User, Category, Watchlist
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class AuctionListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'starting_bid', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'category', 'creator')
    search_fields = ('title', 'description', 'creator__username')

class BidAdmin(admin.ModelAdmin):
    list_display = ('listing', 'bidder', 'bid_amount', 'created_at')
    list_filter = ('listing', 'bidder')
    search_fields = ('listing__title', 'bidder__username')

class CommentAdmin(admin.ModelAdmin):
    list_display = ('listing', 'commenter', 'created_at')
    list_filter = ('listing', 'commenter')
    search_fields = ('listing__title', 'commenter__username', 'comment_text')

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_filter = ('name',)
    search_fields = ('name',)


class WatchListAdmin(BaseUserAdmin):
    list_display = ('creator__username', 'listing')
    list_filter = ('creator__username', 'listing')
    search_fields = ('creator__username' , 'listing')


class CustomUserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )


# Registrando os modelos no admin do Django
admin.site.register(AuctionListing, AuctionListingAdmin)
admin.site.register(Bid, BidAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Watchlist)  