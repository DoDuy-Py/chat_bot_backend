from rest_framework import serializers
from .models import *
from django.utils.timezone import now as djnow


class AccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = Account
        fields = '__all__'
