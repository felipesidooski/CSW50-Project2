from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import User, AuctionListing, Bid, Comment
from .forms import ListingForm, BidForm, CommentForm



def index(request):
    listings = AuctionListing.objects.filter(is_active=True)
    listings_by_category = {}
    # Agrupar os leilões por categoria
    for listing in listings:
        category = listing.category
        if category not in listings_by_category:
            listings_by_category[category] = []
        listings_by_category[category].append(listing)
    # Dividir os leilões de cada categoria em grupos de até 4 itens
    listings_by_category_chunks = {
        category: [listings[i:i+4] for i in range(0, len(listings), 4)]
        for category, listings in listings_by_category.items()
    }
    # Passando os leilões organizados por categoria para o template
    context = {
        'listings_by_category': listings_by_category_chunks,
    }
    return render(request, 'auctions/index.html', context)

@login_required
def create_listing(request):
    if request.method == "POST":
        form = ListingForm(request.POST)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.creator = request.user
            listing.save()
            return redirect('index')
    else:
        form = ListingForm()
    return render(request, 'auctions/create_listing.html', {'form': form})

@login_required
def listing_detail(request, listing_id):
    listing = get_object_or_404(AuctionListing, pk=listing_id)
    bids = listing.bids.all()
    comments = listing.comments.all()
    bid_form = BidForm()
    comment_form = CommentForm()
    message = None  # To hold error message

    if request.method == "POST":
        if 'place_bid' in request.POST:
            bid_form = BidForm(request.POST)
            if bid_form.is_valid():
                bid_amount = bid_form.cleaned_data['bid_amount']
                # Check if the bid is higher than the starting bid and any other existing bids
                if bid_amount >= listing.starting_bid and (not bids or bid_amount > max(bid.bid_amount for bid in bids)):
                    new_bid = bid_form.save(commit=False)
                    new_bid.bidder = request.user
                    new_bid.listing = listing
                    new_bid.save()
                    messages.success(request, "Bid placed successfully!")
                    return redirect('listing_detail', listing_id=listing.id)
                else:
                    message = "Bid must be higher than the current highest bid and the starting bid."
        elif 'add_comment' in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                new_comment = comment_form.save(commit=False)
                new_comment.commenter = request.user
                new_comment.listing = listing
                new_comment.save()
                messages.success(request, "Comment added successfully!")
                return redirect('listing_detail', listing_id=listing.id)

    return render(request, 'auctions/listing_detail.html', {
        'listing': listing,
        'bids': bids,
        'comments': comments,
        'bid_form': bid_form,
        'comment_form': comment_form,
        'message': message
    })

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")



