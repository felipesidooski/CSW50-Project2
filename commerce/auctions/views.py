from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import User, AuctionListing, Bid, Comment, Category
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
    show_new_category_input = False  # Controle para mostrar o campo de nova categoria

    if request.method == "POST":
        form = ListingForm(request.POST)
        selected_category = request.POST.get('category')
        print(f'Selected Category: {selected_category}')
        # Verifica se foi selecionada "New Category"
        if selected_category == "new":
            show_new_category_input = True

        if form.is_valid():
            listing = form.save(commit=False)
            listing.creator = request.user

            if show_new_category_input:
                print(f'Entrou na estrutura de nova categoria!')
                new_category_name = request.POST.get('new_category', '').strip()
                if new_category_name:
                    # Cria ou recupera a nova categoria
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
                # Associa a categoria existente
                print(f'Registrando dentro da estrutura original da pagina')
                listing.category = Category.objects.get(id=selected_category)

            # Salva e redireciona
            print(f'Salvando a estrutura - listing - redirect index')
            listing.save()
            return redirect('index')

        else:
            print(f'Formulario nao aceito!')
            print(f'Form: {form}')

    else:
        print(f'Formulario nao valido!')
        form = ListingForm()

    # Renderiza o formulário
    print(f'Renderizou o formulario pois n~ao conseguiu cadastrar corretamente!')
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
    message = None  # To hold error message

    # Verificar se o usuário atual é o criador da listagem
    is_owner = request.user == listing.creator

    if request.method == "POST":
        # Desativar a listagem se o criador clicar no botão "Deactivate Listing"
        if 'deactivate_listing' in request.POST and is_owner:
            listing.is_active = False
            listing.save()
            messages.success(request, "Listing successfully deactivated.")
            return redirect('index')

        if 'place_bid' in request.POST:
            bid_form = BidForm(request.POST)
            if bid_form.is_valid():
                bid_amount = bid_form.cleaned_data['bid_amount']
                # Verifica se o lance é maior que o lance inicial e os lances existentes
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
        'message': message,
        'is_owner': is_owner,  # Passar a variável para o template
    })



@login_required
def my_listings(request):
    # Recupera todas as listagens do usuário logado
    listings = AuctionListing.objects.filter(creator=request.user)

    # Verifica se o formulário foi enviado para ativar uma listagem
    if request.method == "POST":
        for listing in listings:
            if f'activate_listing_{listing.id}' in request.POST:
                listing.is_active = True
                listing.save()
                messages.success(request, f'Listing "{listing.title}" has been activated.')
                return redirect('my_listings')

    return render(request, 'auctions/my_listings.html', {
        'listings': listings
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



