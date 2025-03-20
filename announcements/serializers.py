from rest_framework import serializers
from .models import Announcement, Category, Review


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'image']


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = Review
        fields = ['id', 'user', 'text', 'rating', 'created_at']


class AnnouncementSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Announcement
        fields = [
            'id', 'title', 'description', 'price', 'location',
            'category', 'category_id', 'created_at', 'updated_at', 'reviews'
        ]

    def validate_price(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Ціна не може бути від'ємною.")
        return value

    def create(self, validated_data):
        category = validated_data.pop('category', None)
        announcement = Announcement.objects.create(**validated_data)
        if category:
            announcement.category = category
            announcement.save()
        return announcement

    def update(self, instance, validated_data):
        category = validated_data.pop('category', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if category:
            instance.category = category
        instance.save()
        return instance
