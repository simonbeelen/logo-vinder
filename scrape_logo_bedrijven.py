from logo_scraper import EigenUrlAfbeeldingScraper
import time

bedrijven = [
    ('Accenture','https://www.accenture.com/be-en'),
    ('Acolad Digital','https://www.acolad.com/nl.html'),
    ('Amista','https://www.amista.be/careers'),
    ('ARHS Group','https://www.arhs-group.com/about-us/'),
    ('Ausy Belgium','https://www.ausy.be'),
    ('Avelon','https://www.avelon.be/'),
    ('Axxes','https://www.axxes.com/'),
    ('B_Robots','https://b-robots.be/'),
    ('Bizztalent','https://www.bizztalent.be/'),
    ('Blents','https://www.blents.be/careers/'),
    ('BNP Paribas Fortis','https://www.bnpparibasfortis.com/jobs'),
    ('Bulls-i','https://www.bulls-i.company/'),
    ('BuSI','https://www.busi.eu'),
    ('Canguru','https://www.cangurusolutions.com'),
    ('Capgemini','https://www.capgemini.com/'),
    ('CHRLY','https://www.chrly.be'),
    ('Colibri Consulting BV','https://www.colibri.consulting'),
    ('Colruyt Group','https://jobs.colruytgroup.com'),
    ('Computacenter','https://www.computacenter.com/en-be/who-we-are'),
    ('Cookie Crunchers','https://www.cookiecrunchers.be/'),
    ('delaware BeLux','https://www.delaware.pro/nl-be/careers/junior'),
    ('Devoteam NV/SA','https://www.linkedin.com/company/devoteam/'),
    ('Dilaco','https://www.linkedin.com/company/dilaco-belgium/mycompany/'),
    ('Eezee-IT','https://eezee-it.com'),
    ('EQUANS','https://jobs.equans.be/nl/'),
    ('Euricom','https://www.linkedin.com/company/euricom/'),
    ('Exclusive Networks','https://www.exclusive-networks.com/be/'),
    ('Fabulor','https://www.fabulor.eu'),
    ('Flexso','https://www.flexso.com'),
    ('Grasshoppers Academy','https://www.ghac.eu'),
    ('Gumption','https://www.gumption.eu'),
    ('Harvey Nash BELGIUM','https://www.harveynash.com'),
    ('ICT Talents','https://www.houseoftalents.be/nl/ict-talents'),
    ('Inetum-Realdolmen','https://www.realdolmen.com'),
    ('Keleos','https://www.linkedin.com/company/keleosbe/'),
    ('Launch.Career','https://launch.career/'),
    ('Nexios IT','https://www.nexiosit.com/'),
    ('Nomios','https://www.nomios.be/'),
    ('Ordina','https://www.ordina.be/'),
    ('Persolis','https://persolis.be/'),
    ('Proclus BV','https://www.proclus.be'),
    ('RP One','https://www.linkedin.com/company/rp-one/mycompany/?viewAsMember=true'),
    ('Safran AES Brussels','https://www.safran-group.com'),
    ('Simac','https://www.simac.be/nl/'),
    ('Smals','https://www.smals.be/nl/jobs'),
    ('Sopra Steria','https://www.soprasteria.be'),
    ('SPIE ICS IT Talent Solutions SA','https://www.spie-ics.be/'),
    ('TheValueChain','https://www.thevaluechain.eu'),
    ('Userfull','https://userfull.be'),
    ('UZ Brussel','https://www.uzbrusselict.be'),
    ('YPTO','https://www.ypto.be/'),
    ('Yteria','https://www.yteria.com')
]

scraper = EigenUrlAfbeeldingScraper()
resultaten = {"succes": [], "mislukt": []}

print(f"Start verwerking van {len(bedrijven)} bedrijven...")
for index, (naam, url) in enumerate(bedrijven):
    try:
        print(f"[{index+1}/{len(bedrijven)}] Verwerken: {naam} ({url})")
        scraper.verwerk(naam, url)
        resultaten["succes"].append(naam)
        print(f"  ✓ Succesvol verwerkt")
        # Kleine pauze tussen requests om overbelasting van servers te voorkomen
        time.sleep(1)
    except Exception as e:
        print(f"  ✗ Fout bij verwerken van {naam}: {str(e)}")
        resultaten["mislukt"].append((naam, url, str(e)))
        # Doorgaan met volgende bedrijf
        continue

# Samenvatting tonen
print("\n--- RESULTATEN SAMENVATTING ---")
print(f"Totaal bedrijven: {len(bedrijven)}")
print(f"Succesvol verwerkt: {len(resultaten['succes'])}")
print(f"Mislukt: {len(resultaten['mislukt'])}")

if resultaten["mislukt"]:
    print("\nMislukte bedrijven:")
    for naam, url, fout in resultaten["mislukt"]:
        print(f"- {naam}: {fout}")
    
    # Optioneel: sla mislukte bedrijven op in een bestand voor later
    with open("mislukte_bedrijven.txt", "w") as f:
        for naam, url, fout in resultaten["mislukt"]:
            f.write(f"{naam},{url},{fout}\n")
    print("\nMislukte bedrijven opgeslagen in 'mislukte_bedrijven.txt'")

print("\nKlaar! Check map 'logos' en database 'eigen_afbeeldingen.db' voor resultaten.")