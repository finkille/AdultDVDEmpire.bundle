# AdultDVDEmpire
# Update: 12 July 2015
# Description: Updated for the changes to the new site.

# URLS
ADE_BASEURL = 'http://www.adultdvdempire.com'
ADE_SEARCH_MOVIES = ADE_BASEURL + '/dvd/search?q=%s'
ADE_MOVIE_INFO = ADE_BASEURL + '/%s/'

def Start():
  HTTP.CacheTime = CACHE_1DAY
  HTTP.SetHeader('User-agent', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)')

class ADEAgent(Agent.Movies):
  name = 'Adult DVD Empire'
  languages = [Locale.Language.English]
  primary_provider = True


  def search(self, results, media, lang):
    title = media.name
    if media.primary_metadata is not None:
      title = media.primary_metadata.title
    
    query = String.URLEncode(String.StripDiacritics(title.replace('-','')))
    # Finds div with class=item
    for movie in HTML.ElementFromURL(ADE_SEARCH_MOVIES % query).xpath('//div[contains(@class, "col-xs-7")]/h3/a[1]'): 
      # curName = The text in the 'title' p
      curName = movie.text_content().strip()
      if curName.count(', The'):
        curName = 'The ' + curName.replace(', The','',1)

      # curID = the ID portion of the href in 'movie'
      curID = movie.get('href').split('/',2)[1]
      score = 100 - Util.LevenshteinDistance(title.lower(), curName.lower())
      if curName.lower().count(title.lower()):
        results.Append(MetadataSearchResult(id = curID, name = curName, score = 100, lang = lang))
      elif (score >= 95):
        results.Append(MetadataSearchResult(id = curID, name = curName, score = score, lang = lang))

    results.Sort('score', descending=True)

  def update(self, metadata, media, lang):
    html = HTML.ElementFromURL(ADE_MOVIE_INFO % metadata.id)
    metadata.title = media.title

    # Thumb and Poster
    try:
      img = html.xpath('//*[@id="front-cover"]/img')[0]
      thumbUrl = img.get('src')

      thumb = HTTP.Request(thumbUrl)
      posterUrl = img.get('src')
      metadata.posters[posterUrl] = Proxy.Preview(thumb)
    except:
      pass

    # Tagline
    try: metadata.tagline = html.xpath('//p[@class="Tagline"]')[0].text_content().strip()
    except: pass

    # Summary.
    try:
      for summary in html.xpath('//*[@id="content"]/div[2]/div[2]/div/p'):
        metadata.summary = summary.text_content()
    except Exception, e:
      Log('Got an exception while parsing summary %s' %str(e))

    # Product info div
    data = {}

    productinfo = HTML.StringFromElement(html.xpath('//*[@id="content"]/div[2]/div[4]/div/div[1]/ul')[0])

    productinfo = productinfo.replace('<small>', '|')
    productinfo = productinfo.replace('</small>', '')
    productinfo = productinfo.replace('<li>', '').replace('</li>', '')
    productinfo = HTML.ElementFromString(productinfo).text_content()

    for div in productinfo.split('|'):
      if ':' in div:
        name, value = div.split(':')
        data[name.strip()] = value.strip()

    # Rating
    if data.has_key('Rating'):
      metadata.content_rating = data['Rating']

    # Studio    
    if data.has_key('Studio'):
      metadata.studio = data['Studio']

    # Release   
    if data.has_key('Released'):
      try:
        metadata.originally_available_at = Datetime.ParseDate(data['Released']).date()
        metadata.year = metadata.originally_available_at.year
      except: pass
 
    # Cast
    try:
      metadata.roles.clear()
      htmlcast = html.xpath('//a[contains(@class, "PerformerName")]')
      for cast in htmlcast:
        cname = cast.text_content().strip()
        if (len(cname) > 0):
          role = metadata.roles.new()
          role.name = cname
    except Exception, e:
      Log('Got an exception while parsing cast %s' %str(e))
