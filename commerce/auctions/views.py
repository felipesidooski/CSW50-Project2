from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import User, AuctionListing, Bid, Comment, Category, Watchlist
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
    listings_by_category_chunks = {
        category: [listings[i:i+4] for i in range(0, len(listings), 4)]
        for category, listings in listings_by_category.items()
    }
    context = {'listings_by_category': listings_by_category_chunks}
    return render(request, 'auctions/index.html', context)

@login_required
def create_listing(request):
    show_new_category_input = False

    if request.method == "POST":
        form = ListingForm(request.POST)
        selected_category = request.POST.get('category')

        if selected_category == "new":
            show_new_category_input = True

        if form.is_valid():
            listing = form.save(commit=False)
            listing.creator = request.user

            if show_new_category_input:
                new_category_name = request.POST.get('new_category', '').strip()
                if new_category_name:
                    category_obj, created = Category.objects.get_or_create(
                        name=new_category_name.lower()
                    )
                    listing.category = category_obj
                else:
                    messages.error(request, "Please provide a name for the new category.")
                    return render(request, 'auctions/create_listing.html', {
                        'form': form,
                        'categories': Category.objects.all(),
                        'show_new_category_input': show_new_category_input
                    })
            else:
                listing.category = Category.objects.get(id=selected_category)

            listing.save()
            return redirect('index')

        messages.error(request, "Invalid form submission.")
    else:
        form = ListingForm()

    return render(request, 'auctions/create_listing.html', {
        'form': form,
        'categories': Category.objects.all(),
        'show_new_category_input': show_new_category_input
    })


@login_required
def listing_detail(request, listing_id):
    listing = get_object_or_404(AuctionListing, pk=listing_id)
    bids = listing.bids.all()
    comments = listing.comments.all()
    bid_form = BidForm()
    comment_form = CommentForm()
    is_owner = request.user == listing.creator

    # Verificar se o listing está na watchlist do usuário
    in_watchlist = Watchlist.objects.filter(user=request.user, listing=listing).exists()

    highest_bid = bids.order_by('-bid_amount').first() if bids.exists() else None
    highest_bidder = highest_bid.bidder if highest_bid else None

    if request.method == "POST":
        if 'place_bid' in request.POST:
            bid_form = BidForm(request.POST)
            if bid_form.is_valid():
                bid_amount = bid_form.cleaned_data['bid_amount']
                if bid_amount >= listing.starting_bid and (not bids or bid_amount > max(bid.bid_amount for bid in bids)):
                    new_bid = bid_form.save(commit=False)
                    new_bid.bidder = request.user
                    new_bid.listing = listing
                    new_bid.save()
                    messages.success(request, "Bid placed successfully!")
                    return redirect('listing_detail', listing_id=listing.id)
                else:
                    messages.error(request, "Bid must be higher than the current highest bid and the starting bid.")
        elif 'add_comment' in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                new_comment = comment_form.save(commit=False)
                new_comment.commenter = request.user
                new_comment.listing = listing
                new_comment.save()
                messages.success(request, "Comment added successfully!")
                return redirect('listing_detail', listing_id=listing.id)
        elif 'deactivate_listing' in request.POST and is_owner:
            listing.is_active = False
            listing.save()
            messages.success(request, "Listing successfully deactivated.")
            return redirect('index')
        elif 'add_to_watchlist' in request.POST:
            # Adicionar o item à watchlist do usuário
            _, created = Watchlist.objects.get_or_create(user=request.user, listing=listing)
            if created:
                messages.success(request, "Element added to your watchlist.")
            else:
                messages.warning(request, "This item is already in your watchlist.")
            return redirect('listing_detail', listing_id=listing_id)
        elif 'remove_from_watchlist' in request.POST:
            watchlist_item = get_object_or_404(Watchlist, user=request.user, listing=listing)
            watchlist_item.delete()
            messages.warning(request, "Element removed from your watchlist.")
            return redirect('listing_detail', listing_id=listing_id)


    return render(request, 'auctions/listing_detail.html', {
        'listing': listing,
        'bids': bids,
        'comments': comments,
        'bid_form': bid_form,
        'comment_form': comment_form,
        'is_owner': is_owner,
        'highest_bid': highest_bid,
        'highest_bidder': highest_bidder,
        'in_watchlist': in_watchlist  # Passar essa variável para o template
    })


@login_required
def add_to_watchlist(request, listing_id):
    listing = get_object_or_404(AuctionListing, id=listing_id)
    _, created = Watchlist.objects.get_or_create(user=request.user, listing=listing)

    if created:
        messages.success(request, "Element added to your watchlist.")
    else:
        messages.info(request, "This item is already in your watchlist.")
    
    return redirect('listing_detail', listing_id=listing_id)

@login_required
def remove_from_watchlist(request, listing_id):
    watchlist_item = get_object_or_404(Watchlist, user=request.user, listing_id=listing_id)
    watchlist_item.delete()
    messages.warning(request, "Element removed from your watchlist.")
    return redirect('listing_detail', listing_id=listing_id)


@login_required
def view_watchlist(request):
    watchlist_items = Watchlist.objects.filter(user=request.user)
    return render(request, 'auctions/watchlist.html', {
        'watchlist_items': watchlist_items
    })

@login_required
def my_listings(request):
    listings = AuctionListing.objects.filter(creator=request.user)

    if request.method == "POST":
        for listing in listings:
            if f'activate_listing_{listing.id}' in request.POST:
                listing.is_active = True
                listing.save()
                messages.success(request, f'Listing "{listing.title}" has been activated.')
                return redirect('my_listings')

    return render(request, 'auctions/my_listings.html', {'listings': listings})

@login_required
def my_bids(request):
    bids = Bid.objects.filter(bidder=request.user).select_related('listing')
    grouped_bids = [bids[i:i + 3] for i in range(0, len(bids), 3)]
    return render(request, 'auctions/my_bids.html', {'grouped_bids': grouped_bids})

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            messages.error(request, "Invalid username and/or password.")
    return render(request, "auctions/login.html")

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]

        if password != confirmation:
            messages.error(request, "Passwords must match.")
        else:
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return HttpResponseRedirect(reverse("index"))
            except IntegrityError:
                messages.error(request, "Username already taken.")
    return render(request, "auctions/register.html")
