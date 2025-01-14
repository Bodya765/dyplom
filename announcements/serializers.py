from rest_framework import serializers
from .models import Announcement, Category, Review


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'user', 'text', 'rating', 'created_at']


class AnnouncementSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    reviews = ReviewSerializer(many=True)

    class Meta:
        model = Announcement
        fields = ['id', 'title', 'description', 'price', 'location', 'category', 'created_at', 'reviews']

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Ціна не може бути від'ємною.")
        return value

    def create(self, validated_data):
        category_data = validated_data.pop('category')
        reviews_data = validated_data.pop('reviews')

        # Create the category instance
        category = Category.objects.create(**category_data)

        # Create the announcement instance
        announcement = Announcement.objects.create(category=category, **validated_data)

        # Create review instances
        for review_data in reviews_data:
            Review.objects.create(announcement=announcement, **review_data)

        return announcement

    def update(self, instance, validated_data):
        category_data = validated_data.pop('category')
        reviews_data = validated_data.pop('reviews')

        # Update the category instance
        instance.category.name = category_data['name']
        instance.category.save()

        # Update the announcement instance
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.price = validated_data.get('price', instance.price)
        instance.location = validated_data.get('location', instance.location)
        instance.save()

        # Update or create reviews
        for review_data in reviews_data:
            review = Review.objects.get(id=review_data['id'])
            review.text = review_data['text']
            review.rating = review_data['rating']
            review.save()

        return instance
