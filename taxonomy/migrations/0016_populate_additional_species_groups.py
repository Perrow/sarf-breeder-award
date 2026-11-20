"""Add the remaining aquarium species groups without modifying existing groups.

Only already-existing genera are linked. Later genus creation is handled by the
species-group membership receiver, without seeding unused genera in test databases.
"""

from django.db import migrations


GROUP_GENERA = {
    "Ciklider": (
        "Abactochromis", "Acarichthys", "Acaronia", "Aequidens", "Altolamprologus", "Amatitlania", "Amphilophus", "Andinoacara",
        "Anomalochromis", "Apistogramma", "Apistogrammoides", "Archocentrus", "Aristochromis", "Asprotilapia", "Astatoreochromis", "Astatotilapia",
        "Astronotus", "Aulonocara", "Aulonocranus", "Australoheros", "Benitochromis", "Benthochromis", "Biotodoma", "Biotoecus",
        "Boulengerochromis", "Buccochromis", "Bujurquina", "Callochromis", "Caquetaia", "Chaetobranchopsis", "Chaetobranchus", "Chalinochromis",
        "Champsochromis", "Chiapaheros", "Chilotilapia", "Chindongo", "Chromidotilapia", "Cichla", "Cichlasoma", "Cleithracara",
        "Copadichromis", "Coptodon", "Crenicara", "Crenicichla", "Cryptoheros", "Ctenochromis", "Ctenopharynx", "Cunningtonia",
        "Cyathopharynx", "Cynotilapia", "Cyphotilapia", "Cyprichromis", "Cyrtocara", "Dicrossus", "Dimidiochromis", "Ectodus",
        "Enantiopus", "Eretmodus", "Etroplus", "Exochochromis", "Fossorochromis", "Geophagus", "Gephyrochromis", "Gnathochromis",
        "Grammatotria", "Greenwoodochromis", "Guianacara", "Gymnogeophagus", "Haplochromis", "Harpagochromis", "Hemichromis", "Hemitaeniochromis",
        "Hemitilapia", "Herichthys", "Heros", "Herotilapia", "Heterotilapia", "Hoplarchus", "Hypselecara", "Hypsophrys",
        "Iodotropheus", "Ivanacara", "Julidochromis", "Krobia", "Labeotropheus", "Labidochromis", "Labrochromis", "Laetacara",
        "Lamprologus", "Lepidiolamprologus", "Lestradea", "Lethrinops", "Lichnochromis", "Limbochromis", "Limnochromis", "Limnotilapia",
        "Lipochromis", "Lobochilotes", "Mayaheros", "Maylandia", "Mazarunia", "Melanochromis", "Mesoheros", "Mesonauta",
        "Microdontochromis", "Mikrogeophagus", "Myaka", "Mylochromis", "Naevochromis", "Nandopsis", "Nannacara", "Nanochromis",
        "Neetroplus", "Neochromis", "Neolamprologus", "Nimbochromis", "Nyassachromis", "Ophthalmotilapia", "Oreochromis", "Otopharynx",
        "Parachromis", "Paracyprichromis", "Paralabidochromis", "Parananochromis", "Paraneetroplus", "Paratilapia", "Paretroplus", "Pelmatolapia",
        "Pelvicachromis", "Petenia", "Petrochromis", "Petrotilapia", "Placidochromis", "Platytaeniodus", "Prognathochromis", "Protomelas",
        "Pseudocrenilabrus", "Pseudotropheus", "Pseudsimochromis", "Pterophyllum", "Ptyochromis", "Pundamilia", "Reganochromis", "Retroculus",
        "Rhamphochromis", "Rocio", "Rubricatochromis", "Sarotherodon", "Satanoperca", "Sciaenochromis", "Serranochromis", "Simochromis",
        "Spathodus", "Steatocranus", "Stigmatochromis", "Symphysodon", "Taeniacara", "Taeniochromis", "Taeniolethrinops", "Tahuantinsuyoa",
        "Tanganicodus", "Teleocichla", "Teleogramma", "Telmatochromis", "Theraps", "Thoracochromis", "Thorichthys", "Thysia",
        "Tilapia", "Tomocichla", "Tramitochromis", "Trematocranus", "Trichromis", "Triglachromis", "Tropheops", "Tropheus",
        "Tyrannochromis", "Uaru", "Variabilichromis", "Vieja", "Xenotilapia", "Yssichromis",
    ),
    "Sugmalar": (
        "Acanthicus", "Ancistrus", "Baryancistrus", "Chaetostoma", "Farlowella", "Hypancistrus", "Hypoptopoma", "Hypostomus",
        "Lasiancistrus", "Loricaria", "Otocinclus", "Panaqolus", "Panaque", "Peckoltia", "Pseudacanthicus", "Pseudolithoxus",
        "Pterygoplichthys", "Rineloricaria", "Sturisoma", "Sturisomatichthys",
    ),
    "Övriga malar": (
        "Acanthodoras", "Acantodoras", "Amblydoras", "Bunocephalus", "Chaca", "Clarias", "Eutropiellus", "Ictalurus",
        "Kryptopterus", "Leiocassis", "Malapterurus", "Microglanis", "Mystus", "Ompok", "Pangasius", "Parauchenoglanis",
        "Pimelodus", "Platydoras", "Platystacus", "Pseudoplatystoma", "Schilbe", "Sorubim", "Synodontis", "Tridensimilis",
    ),
    "Karpliknande fiskar": (
        "Acanthopsis", "Balantiocheilus", "Barbodes", "Barbonymus", "Boraras", "Botia", "Carassius", "Chromobotia",
        "Cobitis", "Crossocheilus", "Cyclocheilichthys", "Cyprinella", "Danio", "Dawkinsia", "Desmopuntius", "Devario",
        "Enteromius", "Epalzeorhynchus", "Esomus", "Garra", "Gyrinocheilus", "Labeo", "Leuciscus", "Misgurnus",
        "Myxocyprinus", "Oliotius", "Osteochilus", "Pangio", "Pethia", "Puntigrus", "Puntius", "Rasbora",
        "Rasboroides", "Rohanella", "Sawbwa", "Sewellia", "Sundadanio", "Syncrossus", "Tanichthys", "Trigonostigma",
        "Yasuhikotakia",
    ),
    "Killifiskar": (
        "Adamas", "Aphanius", "Aphyosemion", "Aplocheilichthys", "Aplocheilus", "Austrofundulus", "Austrolebias", "Chromaphyosemion",
        "Cynopoecilus", "Cyprinodon", "Epiplatys", "Fundulopanchax", "Fundulosoma", "Fundulus", "Garmanella", "Jordanella",
        "Laimosemion", "Lamprichthys", "Leptolebias", "Lucania", "Mesoaphyosemion", "Micropanchax", "Nematolebias", "Neofundulus",
        "Nothobranchius", "Pachypanchax", "Poropanchax", "Procatopus", "Profundulus", "Pterolebias", "Rachovia", "Rivulus",
        "Roloffia", "Simpsonichthys", "Terranatos",
    ),
    "Labyrintfiskar": (
        "Belontia", "Betta", "Ctenops", "Helostoma", "Luciocephalus", "Macropodus", "Malpulutta", "Osphronemus",
        "Parosphromenus", "Pseudosphromenus", "Sphaerichthys", "Trichogaster", "Trichopodus", "Trichopsis",
    ),
    "Levandefödande tandkarpar": (
        "Alfaro", "Belonesox", "Brachyrhaphis", "Carlhubbsia", "Cnesterodon", "Flexipenis", "Gambusia", "Girardinus",
        "Heterandria", "Limia", "Micropoecilia", "Neoheterandria", "Phallichthys", "Phalloceros", "Phalloptychus", "Poecilia",
        "Poeciliopsis", "Priapella", "Priapichthys", "Pseudopoecilia", "Pseudoxiphophorus", "Quintana", "Scolichthys", "Xiphophorus",
    ),
    "Goodeider": (
        "Ameca", "Chapalichthys", "Characodon", "Girardinichthys", "Goodea", "Ilyodon", "Skiffia", "Xenoophorus",
        "Xenotaenia", "Xenotoca", "Zoogoneticus",
    ),
    "Regnbågsfiskar": (
        "Bedotia", "Chilaterina", "Chilatherina", "Glossolepis", "Iriatherina", "Marosatherina", "Melanotaenia", "Rhadinocentrus",
    ),
    "Smörbultar": (
        "Brachygobius", "Chlamydogobius", "Dormitator", "Hypseleotris", "Mogurnda", "Oxyeleotris", "Pandaka", "Periophthalmus",
        "Rhinogobius", "Sicyopterus", "Sicyopus", "Stigmatogobius", "Stiphodon", "Tateurndina",
    ),
    "Blåögonfiskar": (
        "Kiunga", "Popondetta", "Popondichthys", "Pseudomugil", "Scaturiginichthys",
    ),
    "Räkor": (
        "Atya", "Atyoida", "Atyopsis", "Caridina", "Desmocaris", "Macrobrachium", "Neocaridina", "Palaemonetes",
    ),
    "Snäckor": (
        "Anentome", "Brotia", "Celetaia", "Cipangopaludina", "Clea", "Clithon", "Cliton", "Faunus",
        "Filopaludina", "Marisa", "Melanoides", "Nerita", "Neritina", "Planorbarius", "Planorbella", "Pomacea",
        "Septaria", "Tarebia", "Tylomelania",
    ),
    "Grönlingar": (
        "Acanthopsis", "Beaufortia", "Botia", "Chromobotia", "Cobitis", "Gastromyzon", "Homaloptera", "Lepidocephalichthys",
        "Misgurnus", "Nemacheilus", "Pangio", "Pseudogastromyzon", "Schistura", "Sewellia", "Syncrossus", "Yasuhikotakia",
    ),
    "Kulfiskar": (
        "Arothron", "Auriglobus", "Carinotetraodon", "Colomesus", "Dichotomyctere", "Leiodon", "Monotrete", "Pao",
        "Takifugu", "Tetraodon",
    ),
    "Ormhuvudsfiskar": (
        "Channa", "Parachanna",
    ),
    "Risfiskar": (
        "Adrianichthys", "Oryzias", "Xenopoecilus",
    ),
}


def populate_species_groups(apps, schema_editor):
    Genus = apps.get_model("taxonomy", "Genus")
    SpeciesGroup = apps.get_model("taxonomy", "SpeciesGroup")
    alias = schema_editor.connection.alias

    for group_name, genus_names in GROUP_GENERA.items():
        group = SpeciesGroup.objects.using(alias).filter(name__iexact=group_name).first()
        if group is None:
            group = SpeciesGroup.objects.using(alias).create(name=group_name)

        for scientific_name in genus_names:
            genus = Genus.objects.using(alias).filter(
                scientific_name__iexact=scientific_name
            ).first()
            if genus is not None:
                group.genera.add(genus)


class Migration(migrations.Migration):
    dependencies = [
        ("taxonomy", "0015_elite_unrated_breeding_classes"),
    ]

    operations = [
        migrations.RunPython(populate_species_groups, migrations.RunPython.noop),
    ]
