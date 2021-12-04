from django.shortcuts import render, redirect
from datetime import datetime
from django.core.cache import cache
import requests as r

def search(request):
    if request.method == 'POST':
        # Get entered input
        query = request.POST.get('query')
        params = f'q={query}&page=1'

        # if data exists in cache redirect to results
        if f'{query}_1' in cache:
            return redirect(f'/results?{params}')

        # reload page if empty query
        if not query:
            return redirect(search)

        # Store number of times searched in current session and clear last session data
        dt = datetime.now()
        minute, day = str(dt.minute), str(dt.day)
        lastmin, lastday = str(dt.minute-1), str(dt.day-1)
        if lastmin in request.session:
            del request.session[lastmin]
        if lastday in request.session:
            del request.session[lastday]
        request.session[minute] = request.session.get(minute, 0) + 1
        request.session[day] = request.session.get(day, 0) + 1

        # Rate limiting based on session data
        if request.session[minute] > 5:
            return render(request, 'home.html', context={'error': 'per minute api limit exceeded'})
        if request.session[day] > 100:
            return render(request, 'home.html', context={'error': 'per day api limit exceeded'})
 
        return redirect(f'/results?{params}')
    return render(request, 'home.html')

def results(request):
    url = 'http://api.stackexchange.com/2.3/search/advanced?site=stackoverflow'
    query = request.GET.get('q', None)
    page = request.GET.get('page', 1)

    # Fetch cached response if exists
    if f'{query}_{page}' in cache:
        response = cache.get(f'{query}_{page}')
    else:
        # Fetch response from API and store in cache
        response = r.get(f'{url}&q={query}&page={page}').json()
        cache.set(f'{query}_{page}', response, timeout=None)
    
    c = {
        'response': response,
        'nextpage': int(page)+1,
        'prevpage': int(page)-1,
        'query': query,
        'has_more': response['has_more']
    }
    return render(request, 'result.html', context=c)