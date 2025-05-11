import time

def citeste_cnf(nume_fisier):
    clauze = []
    with open(nume_fisier, 'r') as f:
        for linie in f:
            linie = linie.strip()
            if not linie or linie.startswith('c') or linie.startswith('p'):
                continue
            clauza = [int(x) for x in linie.split() if x != '0']
            if clauza:
                clauze.append(clauza)
    return clauze

def dpll(clauze, atribuire, contor_recursie):
    contor_recursie[0] += 1

    while True:
        simplificate = []
        unitate_gasita = False

        for clauza in clauze:
            clauza_noua = []
            satisfacuta = False

            for lit in clauza:
                if lit in atribuire:
                    satisfacuta = True
                    break
                elif -lit in atribuire:
                    continue
                else:
                    clauza_noua.append(lit)

            if satisfacuta:
                continue

            if not clauza_noua:
                return None, contor_recursie

            simplificate.append(clauza_noua)

            if len(clauza_noua) == 1 and clauza_noua[0] not in atribuire and -clauza_noua[0] not in atribuire:
                atribuire.add(clauza_noua[0])
                unitate_gasita = True
                break

        if not simplificate:
            return atribuire, contor_recursie

        if not unitate_gasita:
            break

        clauze = simplificate

    toti_literalii = {}
    for clauza in simplificate:
        for lit in clauza:
            toti_literalii[lit] = True

    for lit in list(toti_literalii.keys()):
        if -lit not in toti_literalii:
            noua_atribuire = atribuire.copy()
            noua_atribuire.add(lit)
            rezultat, contor_recursie = dpll(simplificate, noua_atribuire, contor_recursie)
            if rezultat is not None:
                return rezultat, contor_recursie

    variabile = set(abs(lit) for clauza in simplificate for lit in clauza)
    for var in variabile:
        if var not in atribuire and -var not in atribuire:
            noua_atribuire = atribuire.copy()
            noua_atribuire.add(var)
            rezultat, contor_recursie = dpll(simplificate, noua_atribuire, contor_recursie)
            if rezultat is not None:
                return rezultat, contor_recursie

            noua_atribuire = atribuire.copy()
            noua_atribuire.add(-var)
            rezultat, contor_recursie = dpll(simplificate, noua_atribuire, contor_recursie)
            return rezultat, contor_recursie

    return None, contor_recursie

def rezolva_dpll(nume_fisier):
    clauze = citeste_cnf(nume_fisier)
    contor_recursie = [0]
    start = time.perf_counter()

    rezultat, contor_recursie = dpll(clauze, set(), contor_recursie)
    end = time.perf_counter()

    print("Timp executie: {:.6f} secunde".format(end - start))
    print(f"Numar apeluri recursive: {contor_recursie[0]}")
    return "Satisfiabila" if rezultat is not None else "Nesatisfiabila"

print(rezolva_dpll("test1.cnf"))
