import time

def citeste_cnf(nume_fisier):
    clauze = []
    with open(nume_fisier, 'r') as f:
        for linie in f:
            linie = linie.strip()
            if not linie or linie.startswith('c'):
                continue
            if linie.startswith('p'):
                continue
            clauza = [int(x) for x in linie.split() if x != '0']
            if clauza:
                clauze.append(frozenset(clauza))
    return clauze

def este_tautologie(clauza):
    return any(lit in clauza and -lit in clauza for lit in clauza)

def eliminare_literal_pur(clauze):
    toti_literalii = set()
    for clauza in clauze:
        toti_literalii.update(clauza)

    literali_puri = []
    for lit in toti_literalii:
        if -lit not in toti_literalii:
            literali_puri.append(lit)

    return literali_puri

def propagare_unitara(clauze):
    unitati = []
    clauze_noi = []
    modificat = False

    for clauza in clauze:
        if len(clauza) == 1:
            unitati.append(next(iter(clauza)))
            modificat = True
        else:
            clauze_noi.append(clauza)

    while unitati:
        unitate = unitati.pop(0)
        temp_clauze = []

        for clauza in clauze_noi:
            if unitate in clauza:
                continue
            clauza_noua = clauza - {-unitate}
            if not clauza_noua:
                return None, True
            if len(clauza_noua) == 1:
                noua_unitate = next(iter(clauza_noua))
                if -noua_unitate in unitati or noua_unitate in unitati:
                    continue
                unitati.append(noua_unitate)
                modificat = True
            else:
                temp_clauze.append(clauza_noua)

        clauze_noi = temp_clauze

    return clauze_noi, modificat

def eliminare_variabila(clauze, var):
    clauze_pozitive = []
    clauze_negative = []
    alte_clauze = []

    for clauza in clauze:
        if var in clauza:
            clauze_pozitive.append(clauza)
        elif -var in clauza:
            clauze_negative.append(clauza)
        else:
            alte_clauze.append(clauza)

    clauze_rezultate = alte_clauze.copy()

    for clauza_poz in clauze_pozitive:
        for clauza_neg in clauze_negative:
            rezolventa = (clauza_poz - {var}) | (clauza_neg - {-var})
            if not este_tautologie(rezolventa):
                if all(not rezolventa.issubset(c) for c in clauze_rezultate):
                    clauze_rezultate.append(rezolventa)

    return clauze_rezultate

def algoritm_dp(clauze):
    global numar_clauze_generate
    clauze = [c for c in clauze if not este_tautologie(c)]

    if not clauze:
        return True

    if any(len(c) == 0 for c in clauze):
        return False

    clauze, modificat = propagare_unitara(clauze)
    if clauze is None:
        return False
    if modificat:
        return algoritm_dp(clauze)

    literali_puri = eliminare_literal_pur(clauze)
    if literali_puri:
        clauze_filtrate = [c for c in clauze if not any(
            lit in c for lit in literali_puri)]
        numar_clauze_generate += len(clauze_filtrate)
        return algoritm_dp(clauze_filtrate)

    toate_var = set()
    for clauza in clauze:
        for lit in clauza:
            toate_var.add(abs(lit))

    if not toate_var:
        return True

    var = min(toate_var)

    clauze_noi = eliminare_variabila(clauze, var)
    numar_clauze_generate += len(clauze_noi)
    return algoritm_dp(clauze_noi)

def rezolva_dp(nume_fisier):
    global numar_clauze_generate
    numar_clauze_generate = 0
    clauze = citeste_cnf(nume_fisier)
    start = time.perf_counter()
    rezultat = algoritm_dp(clauze)
    end = time.perf_counter()
    print("Timp executie: {:.6f} secunde".format(end - start))
    print(f"Clauze generate: {numar_clauze_generate}")
    return "Satisfiabila" if rezultat else "Nesatisfiabila"

print(rezolva_dp('test.cnf'))
