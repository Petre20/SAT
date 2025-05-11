import time

def citeste_cnf(nume_fisier):
    clauze = []
    clauza_curenta = []
    with open(nume_fisier, 'r') as fisier:
        for linie in fisier:
            linie = linie.strip()
            if not linie or linie.startswith('c'):
                continue
            if linie.startswith('p'):
                continue
            for literal in linie.split():
                numar = int(literal)
                if numar == 0:
                    if clauza_curenta:
                        clauze.append(clauza_curenta)
                        clauza_curenta = []
                else:
                    clauza_curenta.append(numar)
    return clauze

def este_tautologie(clauza):
    literali = set(clauza)
    for lit in literali:
        if -lit in literali:
            return True
    return False

def rezolva(c1, c2):
    rezolventi = []
    for lit in c1:
        if -lit in c2:
            rezolvent = (c1 - {lit}).union(c2 - {-lit})
            if not rezolvent:
                return [frozenset()]
            if not este_tautologie(rezolvent):
                rezolventi.append(frozenset(rezolvent))
    return rezolventi

def rezolutie_sat(clauze, max_iteratii=10000):
    clauze = [frozenset(clauza) for clauza in clauze]
    clauze = [c for c in clauze if not este_tautologie(c)]

    if any(len(c) == 0 for c in clauze):
        return False

    multime_clauze = set(clauze)
    clauze_noi = set()
    iteratii = 0
    numar_clauze_generate = 0

    while True:
        iteratii += 1
        if iteratii > max_iteratii:
            print("Timpul de rulare a fost depasit!")
            return None

        lista_clauze = list(multime_clauze)
        for i in range(len(lista_clauze)):
            for j in range(i + 1, len(lista_clauze)):
                c1 = lista_clauze[i]
                c2 = lista_clauze[j]
                rezolventi = rezolva(c1, c2)
                for rez in rezolventi:
                    if rez == frozenset():
                        return False
                    if rez not in multime_clauze and rez not in clauze_noi:
                        clauze_noi.add(rez)
                        numar_clauze_generate += 1

        if not clauze_noi:
            print(f"Clauze generate: {numar_clauze_generate}")
            return True

        multime_clauze.update(clauze_noi)
        clauze_noi = set()

clauze = citeste_cnf('test1.cnf')

start = time.perf_counter()
rezultat = rezolutie_sat(clauze)
end = time.perf_counter()

print("Satisfiabila" if rezultat else "Nesatisfiabila")
print(f"Timp executie: {end - start:.6f} secunde")
