# auctions/forms.py

from django import forms
from .models import AuctionListing, Bid, Comment

class ListingForm(forms.ModelForm):
    class Meta:
        model = AuctionListing
        fields = ['title', 'description', 'starting_bid', 'image_url', 'category']
        labels = {
            'starting_bid': 'Valor Inicial (USD)',
        }

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['bid_amount']
        labels = {
            'bid_amount': 'Valor do Lance (USD)',
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['comment_text']
