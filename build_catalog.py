# -*- coding: utf-8 -*-
"""
Builds src/catalog.json from the compact editorial dataset below.
Each row: title | artist | year | genre | bpm | duration(s) | E | D | V | A | I
E = energy, D = danceability, V = valence (positivity),
A = acousticness, I = instrumentalness  (all 0..1)

These are EDITORIAL ESTIMATES, not measured audio features. They are used as
the offline baseline; the "Deep scan" button measures real audio in-browser.
"""
import json, re, unicodedata, hashlib, os

RAW = r"""
Blinding Lights|The Weeknd|2019|Synthpop|171|200|.86|.80|.55|.02|.05
As It Was|Harry Styles|2022|Pop|174|167|.76|.78|.50|.12|.02
Anti-Hero|Taylor Swift|2022|Pop|97|200|.62|.70|.38|.20|.01
Flowers|Miley Cyrus|2023|Pop|118|200|.72|.79|.72|.05|.01
Espresso|Sabrina Carpenter|2024|Pop|104|175|.74|.84|.82|.06|.01
Good Luck, Babe!|Chappell Roan|2024|Pop|117|218|.82|.72|.62|.04|.01
Houdini|Dua Lipa|2023|Dance-Pop|118|185|.84|.85|.70|.02|.04
Levitating|Dua Lipa|2020|Dance-Pop|103|203|.83|.86|.88|.02|.02
Dancing Queen|ABBA|1976|Pop|100|231|.80|.83|.92|.08|.01
Billie Jean|Michael Jackson|1982|Pop|117|294|.78|.92|.72|.02|.06
Like a Prayer|Madonna|1989|Pop|113|341|.78|.76|.66|.05|.02
Royals|Lorde|2013|Alt Pop|85|190|.50|.74|.40|.10|.03
Bad Guy|Billie Eilish|2019|Alt Pop|135|194|.48|.82|.48|.12|.15
Happier Than Ever|Billie Eilish|2021|Alt Pop|91|298|.55|.52|.28|.30|.03
drivers license|Olivia Rodrigo|2021|Pop|84|242|.42|.55|.22|.45|.01
vampire|Olivia Rodrigo|2023|Pop Rock|138|219|.80|.62|.42|.08|.01
Cruel Summer|Taylor Swift|2019|Pop|170|178|.80|.78|.70|.04|.02
Blank Space|Taylor Swift|2014|Pop|96|231|.72|.77|.68|.06|.01
Shape of You|Ed Sheeran|2017|Pop|96|233|.70|.87|.80|.25|.01
Thinking Out Loud|Ed Sheeran|2014|Pop|79|281|.42|.62|.68|.58|.01
Uptown Funk|Mark Ronson ft. Bruno Mars|2014|Funk|115|270|.90|.90|.94|.02|.05
24K Magic|Bruno Mars|2016|Funk|107|226|.86|.88|.92|.02|.04
That's What I Like|Bruno Mars|2016|R&B|67|206|.68|.84|.85|.04|.02
Die With A Smile|Lady Gaga & Bruno Mars|2024|Pop|158|251|.62|.62|.52|.18|.01
Apt.|ROSE & Bruno Mars|2024|Pop|149|169|.84|.78|.78|.03|.01
Beautiful Things|Benson Boone|2024|Pop Rock|105|180|.74|.58|.56|.28|.01
Birds of a Feather|Billie Eilish|2024|Alt Pop|105|210|.58|.70|.62|.18|.01
Please Please Please|Sabrina Carpenter|2024|Pop|108|186|.62|.68|.58|.20|.01
Bad Habit|Steve Lacy|2022|Alt R&B|100|232|.62|.78|.58|.18|.04
Not Like Us|Kendrick Lamar|2024|Hip-Hop|101|274|.84|.90|.72|.02|.04
Luther|Kendrick Lamar & SZA|2024|R&B|78|177|.52|.72|.48|.12|.02
Snooze|SZA|2022|R&B|90|202|.52|.76|.50|.18|.02
Kill Bill|SZA|2022|R&B|88|153|.56|.74|.42|.14|.02
Nights|Frank Ocean|2016|Alt R&B|110|307|.58|.68|.38|.20|.06
Ivy|Frank Ocean|2016|Alt R&B|88|249|.48|.62|.36|.42|.04
Redbone|Childish Gambino|2016|Soul|80|326|.48|.76|.62|.30|.12
Get Lucky|Daft Punk|2013|Disco|116|369|.78|.88|.86|.03|.18
Instant Crush|Daft Punk|2013|Electronic|118|337|.64|.70|.48|.04|.20
One More Time|Daft Punk|2000|French House|123|320|.88|.84|.90|.01|.28
Around the World|Daft Punk|1997|French House|121|427|.82|.84|.76|.01|.48
Strobe|deadmau5|2009|Progressive House|128|634|.72|.68|.42|.02|.82
Levels|Avicii|2011|EDM|126|201|.92|.78|.78|.01|.52
Wake Me Up|Avicii|2013|EDM|124|247|.88|.74|.80|.28|.08
Titanium|David Guetta ft. Sia|2011|EDM|126|245|.88|.68|.62|.02|.06
Clarity|Zedd|2012|EDM|128|271|.86|.66|.64|.02|.30
Lean On|Major Lazer & DJ Snake|2015|Dancehall|98|176|.78|.86|.70|.04|.20
Midnight City|M83|2011|Synthpop|105|244|.84|.64|.62|.02|.38
Nightcall|Kavinsky|2013|Synthwave|87|258|.62|.68|.36|.04|.30
Innerbloom|RUfUS DU SOL|2015|House|122|578|.68|.74|.46|.02|.62
Porcelain|Moby|1999|Ambient|96|241|.38|.58|.30|.20|.55
Avril 14th|Aphex Twin|2001|Modern Classical|76|126|.12|.20|.40|.88|.92
Experience|Ludovico Einaudi|2013|Modern Classical|73|315|.30|.18|.32|.90|.90
Nuvole Bianche|Ludovico Einaudi|2004|Modern Classical|72|353|.18|.14|.34|.92|.94
Clair de Lune|Claude Debussy|1905|Classical|62|300|.10|.12|.38|.92|.95
Gymnopedie No.1|Erik Satie|1888|Classical|60|210|.08|.10|.32|.94|.96
Time|Hans Zimmer|2010|Soundtrack|70|275|.42|.18|.28|.40|.88
Cornfield Chase|Hans Zimmer|2014|Soundtrack|92|128|.52|.24|.48|.30|.78
On the Nature of Daylight|Max Richter|2004|Modern Classical|68|372|.18|.14|.22|.86|.92
Bohemian Rhapsody|Queen|1975|Rock|72|354|.76|.42|.58|.22|.12
Somebody to Love|Queen|1976|Rock|100|296|.78|.52|.72|.18|.06
Sweet Child O' Mine|Guns N' Roses|1987|Rock|125|356|.88|.54|.74|.06|.10
Smells Like Teen Spirit|Nirvana|1991|Grunge|117|301|.96|.50|.44|.02|.12
Come As You Are|Nirvana|1991|Grunge|120|219|.76|.52|.38|.06|.18
Wonderwall|Oasis|1995|Britpop|87|259|.68|.56|.62|.38|.02
Creep|Radiohead|1992|Alt Rock|92|239|.56|.42|.24|.32|.04
No Surprises|Radiohead|1997|Alt Rock|84|229|.28|.38|.26|.52|.10
Karma Police|Radiohead|1997|Alt Rock|82|261|.52|.44|.30|.30|.12
Mr. Brightside|The Killers|2003|Indie Rock|148|223|.92|.62|.68|.02|.04
Somebody Told Me|The Killers|2004|Indie Rock|138|197|.90|.66|.72|.02|.04
Take Me Out|Franz Ferdinand|2004|Indie Rock|142|237|.90|.72|.72|.02|.06
Do I Wanna Know?|Arctic Monkeys|2013|Indie Rock|85|272|.66|.66|.40|.08|.12
505|Arctic Monkeys|2007|Indie Rock|78|253|.58|.50|.32|.34|.08
Fluorescent Adolescent|Arctic Monkeys|2007|Indie Rock|133|233|.86|.68|.72|.04|.04
The Less I Know The Better|Tame Impala|2015|Psychedelic|116|216|.70|.72|.56|.04|.12
Let It Happen|Tame Impala|2015|Psychedelic|122|467|.82|.70|.58|.02|.32
Borderline|Tame Impala|2019|Psychedelic|100|237|.68|.76|.58|.06|.10
Electric Feel|MGMT|2007|Psychedelic|112|229|.78|.82|.74|.03|.12
Kids|MGMT|2007|Indie Pop|112|303|.84|.76|.72|.02|.14
Pumped Up Kicks|Foster the People|2010|Indie Pop|128|239|.72|.80|.60|.12|.06
Ho Hey|The Lumineers|2012|Folk Rock|80|163|.58|.64|.74|.68|.02
Sweater Weather|The Neighbourhood|2012|Indie Rock|96|240|.62|.66|.48|.14|.06
Riptide|Vance Joy|2013|Indie Folk|100|204|.68|.74|.82|.62|.01
Budapest|George Ezra|2013|Folk Pop|100|201|.66|.76|.78|.48|.01
Shut Up and Dance|WALK THE MOON|2014|Pop Rock|128|199|.90|.76|.88|.02|.02
Stressed Out|Twenty One Pilots|2015|Alt Pop|85|202|.62|.74|.44|.16|.04
Heathens|Twenty One Pilots|2016|Alt Pop|90|180|.60|.72|.38|.14|.06
Believer|Imagine Dragons|2017|Rock|125|204|.92|.66|.58|.04|.04
Radioactive|Imagine Dragons|2012|Rock|87|187|.86|.52|.48|.10|.08
Numb|Linkin Park|2003|Nu Metal|110|186|.88|.58|.36|.04|.06
In the End|Linkin Park|2000|Nu Metal|106|216|.90|.56|.38|.06|.06
Enter Sandman|Metallica|1991|Metal|123|332|.98|.42|.38|.01|.20
Master of Puppets|Metallica|1986|Metal|106|515|.98|.38|.36|.01|.34
Paint It Black|The Rolling Stones|1966|Rock|98|202|.74|.58|.38|.20|.18
Stairway to Heaven|Led Zeppelin|1971|Rock|82|482|.62|.42|.52|.48|.28
Hotel California|Eagles|1976|Rock|75|391|.62|.52|.48|.38|.22
Dreams|Fleetwood Mac|1977|Soft Rock|105|257|.58|.72|.68|.24|.06
The Chain|Fleetwood Mac|1977|Soft Rock|106|271|.72|.62|.48|.22|.14
September|Earth, Wind & Fire|1978|Funk|126|215|.88|.86|.94|.04|.10
Superstition|Stevie Wonder|1972|Funk|100|245|.82|.84|.80|.06|.12
What's Going On|Marvin Gaye|1971|Soul|90|232|.48|.72|.52|.32|.10
Ain't No Sunshine|Bill Withers|1971|Soul|78|124|.28|.56|.26|.68|.04
Lean on Me|Bill Withers|1972|Soul|78|257|.42|.62|.66|.62|.02
Lovely Day|Bill Withers|1977|Soul|96|255|.52|.78|.88|.22|.06
At Last|Etta James|1960|Soul|62|182|.32|.48|.62|.58|.08
Respect|Aretha Franklin|1967|Soul|115|147|.82|.82|.86|.08|.06
I Will Always Love You|Whitney Houston|1992|R&B|67|271|.52|.48|.58|.40|.02
Crazy in Love|Beyonce|2003|R&B|100|236|.88|.80|.84|.02|.04
Single Ladies|Beyonce|2008|R&B|96|193|.86|.88|.82|.01|.04
Yeah!|Usher|2004|R&B|105|250|.92|.86|.86|.01|.06
No Diggity|Blackstreet|1996|R&B|92|312|.72|.88|.78|.02|.04
Say My Name|Destiny's Child|1999|R&B|88|240|.68|.82|.68|.04|.02
Love on Top|Beyonce|2011|R&B|93|267|.80|.82|.92|.03|.02
Adorn|Miguel|2012|R&B|92|193|.58|.76|.66|.10|.06
Untitled (How Does It Feel)|D'Angelo|2000|Neo Soul|62|434|.38|.62|.44|.34|.18
On & On|Erykah Badu|1997|Neo Soul|88|235|.42|.78|.56|.30|.08
Lose Yourself|Eminem|2002|Hip-Hop|171|326|.92|.74|.46|.02|.02
Stan|Eminem|2000|Hip-Hop|88|404|.60|.68|.28|.16|.04
Juicy|The Notorious B.I.G.|1994|Hip-Hop|94|313|.68|.84|.78|.04|.04
California Love|2Pac|1995|Hip-Hop|92|300|.84|.88|.82|.02|.06
Nuthin' but a 'G' Thang|Dr. Dre|1992|Hip-Hop|95|238|.72|.88|.78|.02|.10
C.R.E.A.M.|Wu-Tang Clan|1993|Hip-Hop|86|252|.52|.72|.32|.08|.06
Ms. Jackson|OutKast|2000|Hip-Hop|90|270|.74|.84|.62|.08|.04
Hey Ya!|OutKast|2003|Hip-Hop|160|235|.92|.82|.92|.06|.04
Gold Digger|Kanye West|2005|Hip-Hop|84|208|.84|.88|.76|.04|.04
Stronger|Kanye West|2007|Hip-Hop|104|311|.90|.76|.68|.02|.12
Runaway|Kanye West|2010|Hip-Hop|86|548|.58|.58|.28|.22|.18
N.Y. State of Mind|Nas|1994|Hip-Hop|88|294|.62|.76|.38|.06|.06
Alright|Kendrick Lamar|2015|Hip-Hop|108|219|.78|.78|.62|.04|.06
HUMBLE.|Kendrick Lamar|2017|Hip-Hop|150|177|.88|.90|.58|.01|.04
Sunflower|Post Malone & Swae Lee|2018|Pop Rap|90|158|.62|.78|.78|.20|.02
Circles|Post Malone|2019|Pop Rap|120|215|.64|.72|.52|.24|.02
God's Plan|Drake|2018|Hip-Hop|77|198|.58|.82|.62|.04|.04
Hotline Bling|Drake|2015|Hip-Hop|67|267|.52|.84|.58|.06|.08
SICKO MODE|Travis Scott|2018|Hip-Hop|155|312|.92|.84|.62|.02|.08
Mask Off|Future|2017|Hip-Hop|135|204|.72|.88|.52|.02|.06
Bad and Boujee|Migos|2016|Hip-Hop|127|183|.76|.88|.62|.02|.06
Old Town Road|Lil Nas X|2019|Country Rap|136|157|.72|.84|.80|.28|.02
Truth Hurts|Lizzo|2017|Pop Rap|158|173|.82|.84|.80|.02|.02
Industry Baby|Lil Nas X|2021|Hip-Hop|114|212|.86|.82|.78|.02|.04
First Class|Jack Harlow|2022|Hip-Hop|106|173|.74|.86|.78|.04|.04
Just Wanna Rock|Lil Uzi Vert|2022|Hip-Hop|148|123|.94|.84|.66|.01|.06
Despacito|Luis Fonsi ft. Daddy Yankee|2017|Latin Pop|89|229|.78|.86|.88|.18|.02
Gasolina|Daddy Yankee|2004|Reggaeton|95|192|.90|.88|.84|.02|.06
Dakiti|Bad Bunny & Jhay Cortez|2020|Reggaeton|92|205|.68|.82|.68|.04|.10
Titi Me Pregunto|Bad Bunny|2022|Reggaeton|130|243|.86|.86|.76|.04|.06
La Bamba|Los Lobos|1987|Latin Rock|142|174|.88|.78|.90|.18|.06
Smooth|Santana ft. Rob Thomas|1999|Latin Rock|116|295|.80|.76|.78|.16|.12
Jerusalema|Master KG|2019|Afrobeats|112|232|.80|.88|.88|.06|.12
Essence|Wizkid ft. Tems|2020|Afrobeats|100|248|.62|.82|.76|.14|.06
Water|Tyla|2023|Amapiano|116|200|.72|.88|.78|.08|.06
Calm Down|Rema & Selena Gomez|2022|Afrobeats|106|240|.70|.84|.80|.10|.04
Gangnam Style|PSY|2012|K-Pop|132|219|.92|.82|.84|.01|.08
Dynamite|BTS|2020|K-Pop|114|199|.84|.82|.92|.02|.02
Butter|BTS|2021|K-Pop|110|164|.82|.84|.88|.02|.02
How You Like That|BLACKPINK|2020|K-Pop|130|181|.90|.78|.76|.01|.04
Super Shy|NewJeans|2023|K-Pop|148|174|.78|.84|.80|.04|.02
Three Little Birds|Bob Marley|1977|Reggae|74|180|.48|.78|.92|.40|.06
Could You Be Loved|Bob Marley|1980|Reggae|104|236|.72|.84|.82|.22|.10
Red Red Wine|UB40|1983|Reggae|88|182|.52|.80|.80|.30|.08
Tum Hi Ho|Arijit Singh|2013|Bollywood|80|262|.38|.48|.32|.58|.04
Chaiyya Chaiyya|A.R. Rahman|1998|Bollywood|100|408|.82|.80|.80|.18|.12
Kal Ho Naa Ho|Sonu Nigam|2003|Bollywood|88|322|.52|.56|.48|.52|.06
Kesariya|Arijit Singh|2022|Bollywood|92|268|.52|.62|.58|.48|.04
Raataan Lambiyan|Asees Kaur & Tanishk Bagchi|2021|Bollywood|96|229|.58|.70|.68|.40|.04
Heeriye|Jasleen Royal & Arijit Singh|2023|Bollywood|100|202|.60|.72|.66|.52|.02
Chaleya|Arijit Singh & Shilpa Rao|2023|Bollywood|108|220|.66|.76|.72|.32|.04
O Maahi|Arijit Singh|2023|Bollywood|96|235|.52|.64|.58|.46|.02
Sajni|Arijit Singh|2024|Bollywood|92|184|.48|.60|.56|.56|.02
Tauba Tauba|Karan Aujla|2024|Punjabi Pop|102|202|.78|.86|.80|.06|.04
Cheques|Shubh|2021|Punjabi Hip-Hop|92|202|.66|.82|.58|.06|.08
Brown Munde|AP Dhillon|2020|Punjabi Hip-Hop|96|236|.68|.84|.66|.06|.08
Excuses|AP Dhillon|2020|Punjabi Pop|94|178|.60|.80|.56|.10|.06
Katchi Sera|Sai Abhyankkar|2024|Indie Pop|104|214|.70|.80|.74|.22|.04
Hukum|Anirudh Ravichander|2023|Kollywood|128|224|.88|.76|.70|.06|.10
Arabic Kuthu|Anirudh Ravichander|2022|Kollywood|130|244|.90|.82|.80|.08|.08
Aasa Kooda|Sai Abhyankkar|2024|Indie Pop|110|196|.70|.82|.76|.20|.04
Husn|Anuv Jain|2023|Indie Folk|88|218|.32|.52|.40|.78|.02
Baarishein|Anuv Jain|2019|Indie Folk|84|236|.30|.50|.34|.82|.02
Kho Gaye Hum Kahan|Prateek Kuhad|2015|Indie Folk|100|214|.42|.58|.52|.72|.04
cold/mess|Prateek Kuhad|2018|Indie Folk|96|226|.38|.56|.44|.70|.04
Take Five|Dave Brubeck|1959|Jazz|88|324|.48|.62|.64|.66|.78
So What|Miles Davis|1959|Jazz|136|545|.58|.58|.56|.68|.82
Autumn Leaves|Nat King Cole|1955|Jazz|72|180|.28|.48|.38|.78|.48
Fly Me to the Moon|Frank Sinatra|1964|Jazz|120|148|.52|.66|.78|.54|.28
Feeling Good|Nina Simone|1965|Jazz|68|175|.56|.52|.66|.56|.18
La Vie En Rose|Edith Piaf|1947|Chanson|84|187|.28|.50|.58|.76|.10
What a Wonderful World|Louis Armstrong|1967|Jazz|72|140|.26|.52|.88|.72|.16
Moon River|Audrey Hepburn|1961|Standard|76|158|.22|.46|.60|.82|.12
Weightless|Marconi Union|2011|Ambient|60|480|.12|.30|.42|.40|.88
An Ending (Ascent)|Brian Eno|1983|Ambient|60|264|.10|.16|.40|.34|.92
Deep Blue Day|Brian Eno|1983|Ambient|68|231|.14|.24|.44|.62|.86
A Walk|Tycho|2012|Downtempo|110|317|.48|.62|.58|.20|.72
Sunset Lover|Petit Biscuit|2015|Electronic|120|233|.56|.72|.66|.12|.62
Ocean Eyes|Billie Eilish|2016|Alt Pop|72|200|.32|.58|.42|.48|.08
Someone Like You|Adele|2011|Pop|67|285|.34|.42|.24|.72|.02
Hello|Adele|2015|Pop|79|295|.48|.48|.34|.46|.02
Rolling in the Deep|Adele|2010|Soul Pop|105|228|.78|.68|.48|.22|.02
Skyfall|Adele|2012|Pop|76|286|.48|.44|.34|.40|.06
Jolene|Dolly Parton|1973|Country|112|160|.54|.64|.48|.68|.04
Ring of Fire|Johnny Cash|1963|Country|107|155|.56|.66|.60|.62|.08
Hurt|Johnny Cash|2002|Country|94|218|.28|.40|.18|.66|.06
The Sound of Silence|Simon & Garfunkel|1964|Folk|108|190|.32|.46|.30|.78|.04
Blowin' in the Wind|Bob Dylan|1963|Folk|82|168|.30|.52|.48|.84|.02
Like a Rolling Stone|Bob Dylan|1965|Rock|95|369|.72|.56|.52|.32|.10
Fast Car|Tracy Chapman|1988|Folk|106|296|.48|.62|.46|.72|.04
Landslide|Fleetwood Mac|1975|Folk Rock|82|199|.26|.44|.34|.80|.04
Heartbeats|Jose Gonzalez|2003|Indie Folk|92|172|.32|.56|.50|.82|.06
Skinny Love|Bon Iver|2007|Indie Folk|82|238|.30|.42|.28|.78|.08
Holocene|Bon Iver|2011|Indie Folk|86|337|.36|.40|.36|.68|.24
Motion Sickness|Phoebe Bridgers|2017|Indie Rock|92|240|.52|.54|.34|.42|.08
Kyoto|Phoebe Bridgers|2020|Indie Rock|118|224|.66|.62|.48|.20|.08
I Know the End|Phoebe Bridgers|2020|Indie Rock|90|300|.70|.48|.36|.28|.10
The Night We Met|Lord Huron|2015|Indie Folk|76|208|.30|.46|.26|.70|.06
Space Song|Beach House|2015|Dream Pop|96|260|.48|.58|.42|.20|.24
Silver Springs|Fleetwood Mac|1977|Soft Rock|96|284|.62|.58|.44|.30|.08
Yellow|Coldplay|2000|Alt Rock|88|269|.54|.52|.58|.36|.08
Clocks|Coldplay|2002|Alt Rock|131|310|.70|.56|.52|.12|.22
Viva La Vida|Coldplay|2008|Pop Rock|138|241|.78|.58|.68|.16|.10
Fix You|Coldplay|2005|Alt Rock|68|295|.44|.42|.40|.36|.12
A Sky Full of Stars|Coldplay|2014|EDM|125|268|.88|.72|.76|.04|.12
"""

KEYS = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

out, seen = [], set()
for line in RAW.strip().splitlines():
    p = [x.strip() for x in line.split("|")]
    if len(p) != 11:
        raise ValueError("bad row: " + line)
    title, artist, year, genre, bpm, dur, E, D, V, A, I = p
    sid = slug(title + "-" + artist)
    if sid in seen:
        continue
    seen.add(sid)
    h = int(hashlib.sha1(sid.encode()).hexdigest()[:8], 16)
    rec = {
        "id": sid,
        "title": title, "artist": artist,
        "year": int(year), "genre": genre,
        "bpm": int(bpm), "duration": int(dur),
        "key": KEYS[h % 12] + (" minor" if (h >> 4) % 3 == 0 else " major"),
        "loudness": round(-13.5 + float(E) * 7.5 - float(A) * 1.2, 1),
        "f": {"energy": float(E), "dance": float(D), "valence": float(V),
              "acoustic": float(A), "instrumental": float(I)},
        "origin": "catalog",
    }
    out.append(rec)

here = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(here, "src", "catalog.json")
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
print("wrote", len(out), "songs ->", path, os.path.getsize(path), "bytes")
