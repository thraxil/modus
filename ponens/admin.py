from django.contrib import admin
from models import *

class PredicateAdmin(admin.ModelAdmin):
    prepopulated_fields = {'name' : ("label",)}
admin.site.register(Predicate,PredicateAdmin)
    
class ExpressionAdmin(admin.ModelAdmin): pass
admin.site.register(Expression,ExpressionAdmin)

class TermAdmin(admin.ModelAdmin): pass
admin.site.register(Term,TermAdmin)

class RuleAdmin(admin.ModelAdmin):
    prepopulated_fields = {'name' : ("label",)}
admin.site.register(Rule,RuleAdmin)
    
