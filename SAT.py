import time
import psutil
import os

class SATSolver:
    def __init__(self):
        self.stats = {
            'dp_clauses_generated': 0,
            'dpll_recursive_calls': 0,
            'resolution_clauses_generated': 0
        }
        self.process = psutil.Process(os.getpid())
    
    def get_memory_usage(self):
        """Returnează utilizarea de memorie în MB"""
        return self.process.memory_info().rss / 1024 / 1024
    
    def get_cpu_times(self):
        """Returnează timpul total de CPU (user + system) în secunde"""
        cpu_times = self.process.cpu_times()
        return cpu_times.user + cpu_times.system
    
    def citeste_cnf(self, nume_fisier):
        """Citește fișierul CNF și returnează listele de clauze pentru fiecare algoritm"""
        clauze_dp = []
        clauze_dpll = []
        clauze_resolution = []
        
        with open(nume_fisier, 'r') as f:
            for linie in f:
                linie = linie.strip()
                if not linie or linie.startswith('c') or linie.startswith('p'):
                    continue
                clauza = [int(x) for x in linie.split() if x != '0']
                if clauza:
                    clauze_dp.append(frozenset(clauza))
                    clauze_dpll.append(clauza)
                    clauze_resolution.append(clauza)
        
        return clauze_dp, clauze_dpll, clauze_resolution
    
    # ===== ALGORITM DAVIS-PUTNAM =====
    def este_tautologie(self, clauza):
        """Verifică dacă clauza este tautologie (conține p și -p)"""
        literali = set(clauza) if isinstance(clauza, (list, tuple)) else clauza
        for lit in literali:
            if -lit in literali:
                return True
        return False
    
    def eliminare_literal_pur(self, clauze):
        """Găsește și returnează literalii puri (care apar doar în formă pozitivă sau negativă)"""
        toti_literalii = set()
        for clauza in clauze:
            toti_literalii.update(clauza)
        
        literali_puri = []
        for lit in toti_literalii:
            if -lit not in toti_literalii:
                literali_puri.append(lit)
        
        return literali_puri
    
    def propagare_unitara(self, clauze):
        """Aplică propagarea unitară până la saturație"""
        modificat = True
        while modificat:
            modificat = False
            clauze_noi = []
            
            # Gaseste clausele unitare
            unitati = []
            for clauza in clauze:
                if len(clauza) == 1:
                    unitati.append(next(iter(clauza)))
                else:
                    clauze_noi.append(clauza)
            
            if not unitati:
                break
            
            # Aplica propagarea pentru fiecare literal unitar
            for unitate in unitati:
                temp_clauze = []
                
                for clauza in clauze_noi:
                    if unitate in clauza:
                        # Clauza este satisfăcuta, o eliminăm
                        continue
                    elif -unitate in clauza:
                        # Eliminam literalul din clauza
                        clauza_noua = clauza - {-unitate}
                        if not clauza_noua:
                            # Clauza goala - conflict
                            return None, True
                        temp_clauze.append(clauza_noua)
                    else:
                        # Clauza nu este afectata
                        temp_clauze.append(clauza)
                
                clauze_noi = temp_clauze
                modificat = True
            
            clauze = clauze_noi
        
        return clauze, len(clauze) == 0
    
    def eliminare_variabila(self, clauze, var):
        """Elimină variabila prin rezoluție - versiune corectată"""
        clauze_pozitive = []
        clauze_negative = []
        clauze_neutrale = []
        
        # Separam clausele în functie de aparitia variabilei
        for clauza in clauze:
            if var in clauza:
                clauze_pozitive.append(clauza)
            elif -var in clauza:
                clauze_negative.append(clauza)
            else:
                clauze_neutrale.append(clauza)
        
        # Incepem cu clauzele care nu contin variabila
        clauze_rezultate = set(clauze_neutrale)
        
        # Daca nu avem ambele tipuri de clauze, pastram toate clauzele
        if not clauze_pozitive or not clauze_negative:
            # Daca avem doar clauze pozitive sau doar negative, pastram toate
            clauze_rezultate.update(clauze_pozitive)
            clauze_rezultate.update(clauze_negative)
            return list(clauze_rezultate)
        
        # Generam rezolventele intre clausele pozitive si negative
        for clauza_poz in clauze_pozitive:
            for clauza_neg in clauze_negative:
                # Rezolventa = (clauza_poz - {var}) ∪ (clauza_neg - {-var})
                rezolventa = (clauza_poz - {var}) | (clauza_neg - {-var})
                
                # Daca rezolventa este goala, avem o contradictie
                if len(rezolventa) == 0:
                    return [frozenset()]  # Clauza goala
                
                # Verificam daca rezolventa este tautologie
                if not self.este_tautologie(rezolventa):
                    clauze_rezultate.add(rezolventa)
        
        # Eliminam subsumtiile
        clauze_finale = []
        lista_rezultate = list(clauze_rezultate)
        
        for i, clauza1 in enumerate(lista_rezultate):
            subsumita = False
            for j, clauza2 in enumerate(lista_rezultate):
                if i != j and clauza2.issubset(clauza1):
                    subsumita = True
                    break
            if not subsumita:
                clauze_finale.append(clauza1)
        
        return clauze_finale
    
    def algoritm_dp(self, clauze):
        """Algoritmul Davis-Putnam corectat"""
        # Eliminam tautologiile
        clauze = [c for c in clauze if not self.este_tautologie(c)]
        
        # Cazul de baza: multimea goala de clauze
        if not clauze:
            return True
        
        # Cazul de baza: există clauza goala
        if any(len(c) == 0 for c in clauze):
            return False
        
        # Aplicam propagarea unitara
        clauze, satisfiabila = self.propagare_unitara(clauze)
        if clauze is None:  # Conflict in propagarea unitara
            return False
        if satisfiabila:  # Nu mai sunt clauze - satisfiabila
            return True
        
        # Eliminam literalii puri
        literali_puri = self.eliminare_literal_pur(clauze)
        if literali_puri:
            # Eliminam toate clausele care contin literali puri
            clauze_filtrate = []
            for clauza in clauze:
                if not any(lit in clauza for lit in literali_puri):
                    clauze_filtrate.append(clauza)
            self.stats['dp_clauses_generated'] += len(clauze_filtrate)
            return self.algoritm_dp(clauze_filtrate)
        
        # Alegem o variabila pentru eliminare
        toate_var = set()
        for clauza in clauze:
            for lit in clauza:
                toate_var.add(abs(lit))
        
        if not toate_var:
            return True
        
        # Alegem variabila care apare in cele mai multe clauze (euristica imbunatatita)
        contor_var = {}
        for var in toate_var:
            contor_var[var] = 0
            for clauza in clauze:
                if var in clauza or -var in clauza:
                    contor_var[var] += 1
        
        var = max(contor_var, key=contor_var.get)
        
        # Eliminam variabila prin rezolutie
        clauze_noi = self.eliminare_variabila(clauze, var)
        self.stats['dp_clauses_generated'] += len(clauze_noi)
        
        return self.algoritm_dp(clauze_noi)
    
    # ===== ALGORITM DPLL =====
    def simplifica_clauze(self, clauze, atribuire):
        """Simplifica clausele pe baza atribuirii curente"""
        clauze_noi = []
        
        for clauza in clauze:
            clauza_noua = []
            clauza_satisfacuta = False
            
            for literal in clauza:
                if literal in atribuire:
                    # Literalul este adevarat, deci clauza este satisfăcuta
                    clauza_satisfacuta = True
                    break
                elif -literal not in atribuire:
                    # Literalul nu este inca atribuit
                    clauza_noua.append(literal)
            
            if not clauza_satisfacuta:
                if not clauza_noua:
                    # Clauza goala - conflict
                    return None
                clauze_noi.append(clauza_noua)
        
        return clauze_noi
    
    def gaseste_literali_unitari(self, clauze):
        """Găsește literalii unitari (din clauze cu un singur literal)"""
        literali_unitari = []
        for clauza in clauze:
            if len(clauza) == 1:
                literali_unitari.append(clauza[0])
        return literali_unitari
    
    def gaseste_literali_puri(self, clauze):
        """Găsește literalii puri în clausele date"""
        toti_literalii = set()
        for clauza in clauze:
            toti_literalii.update(clauza)
        
        literali_puri = []
        for literal in toti_literalii:
            if -literal not in toti_literalii:
                literali_puri.append(literal)
        
        return literali_puri
    
    def dpll(self, clauze, atribuire):
        """Algoritmul DPLL"""
        self.stats['dpll_recursive_calls'] += 1
        
        # Simplifica clauzele pe baza atribuirii curente
        clauze_simplificate = self.simplifica_clauze(clauze, atribuire)
        
        # Verifica conflictul (clauza goala)
        if clauze_simplificate is None:
            return None
        
        # Verifica satisfiabilitatea (nu mai sunt clauze)
        if not clauze_simplificate:
            return atribuire
        
        # Propagarea unitara
        while True:
            literali_unitari = self.gaseste_literali_unitari(clauze_simplificate)
            if not literali_unitari:
                break
            
            # Adauga literalii unitari la atribuire
            for literal in literali_unitari:
                if -literal in atribuire:
                    # Conflict: avem si literal si -literal
                    return None
                atribuire.add(literal)
            
            # Simplifica din nou cu noua atribuire
            clauze_simplificate = self.simplifica_clauze(clauze_simplificate, atribuire)
            
            if clauze_simplificate is None:
                return None
            if not clauze_simplificate:
                return atribuire
        
        # Eliminarea literalilor puri
        literali_puri = self.gaseste_literali_puri(clauze_simplificate)
        if literali_puri:
            for literal in literali_puri:
                if -literal in atribuire:
                    # Conflict: avem si literal si -literal
                    return None
                atribuire.add(literal)
            
            # Simplifica din nou cu noua atribuire
            clauze_simplificate = self.simplifica_clauze(clauze_simplificate, atribuire)
            
            if clauze_simplificate is None:
                return None
            if not clauze_simplificate:
                return atribuire
        
        # Alegerea variabilei pentru branching
        variabile_neatribuite = set()
        for clauza in clauze_simplificate:
            for literal in clauza:
                var = abs(literal)
                if var not in atribuire and -var not in atribuire:
                    variabile_neatribuite.add(var)
        
        if not variabile_neatribuite:
            return atribuire
        
        # Alege prima variabila disponibila
        var = min(variabile_neatribuite)
        
        # Incearca prima ramura (var = True)
        noua_atribuire = atribuire.copy()
        noua_atribuire.add(var)
        rezultat = self.dpll(clauze, noua_atribuire)
        if rezultat is not None:
            return rezultat
        
        # Incearca a doua ramura (var = False)
        noua_atribuire = atribuire.copy()
        noua_atribuire.add(-var)
        return self.dpll(clauze, noua_atribuire)
    
    # ===== ALGORITM REZOLUTIE =====
    def este_tautologie_resolution(self, clauza):
        """Verifică dacă clauza este tautologie"""
        literali = set(clauza)
        for lit in literali:
            if -lit in literali:
                return True
        return False
    
    def rezolva(self, c1, c2):
        """Calculeaza rezolventa intre doua clauze"""
        # Gaseste toate perechile de literali complementari
        perechi_complementare = []
        for lit in c1:
            if -lit in c2:
                perechi_complementare.append(lit)
        
        # Rezolutia functionează doar dacă exista exact o pereche complementara
        if len(perechi_complementare) != 1:
            return []
        
        lit = perechi_complementare[0]
        rezolvent = (c1 - {lit}) | (c2 - {-lit})
        
        # Verificam daca rezolventa este tautologie
        if self.este_tautologie_resolution(rezolvent):
            return []
        
        return [frozenset(rezolvent)]
    
    def rezolutie_sat(self, clauze, max_iteratii=10000):
        """Algoritmul de rezolutie pentru SAT"""
        # Convertim toate clauzele la frozenset si eliminam tautologiile
        clauze = [frozenset(clauza) for clauza in clauze]
        clauze = [c for c in clauze if not self.este_tautologie_resolution(c)]
        
        # Verificam daca exista deja clauza goala
        if any(len(c) == 0 for c in clauze):
            return False
        
        multime_clauze = set(clauze)
        iteratii = 0
        
        while True:
            iteratii += 1
            if iteratii > max_iteratii:
                print("Timpul de rulare a fost depasit!")
                return None
            
            clauze_noi = set()
            lista_clauze = list(multime_clauze)
            
            # Incearca sa rezolve fiecare pereche de clauze
            for i in range(len(lista_clauze)):
                for j in range(i + 1, len(lista_clauze)):
                    c1 = lista_clauze[i]
                    c2 = lista_clauze[j]
                    
                    rezolventi = self.rezolva(c1, c2)
                    for rez in rezolventi:
                        if len(rez) == 0:
                            # Am gasit clauza goala - formula este UNSAT
                            return False
                        
                        if rez not in multime_clauze:
                            clauze_noi.add(rez)
                            self.stats['resolution_clauses_generated'] += 1
            
            # Daca nu am generat clauze noi, algoritmul se opreste
            if not clauze_noi:
                return True
            
            # Adaugam clauzele noi la multimea existenta
            multime_clauze.update(clauze_noi)
    
    def rezolva_toate(self, nume_fisier):
        """Rezolvă problemă SAT cu toate cele 3 algoritmi și afișează rezultatele"""
        print(f"Rezolvarea fișierului: {nume_fisier}")
        print("=" * 80)
        
        clauze_dp, clauze_dpll, clauze_resolution = self.citeste_cnf(nume_fisier)
        
        # Reseteaza statisticile
        self.stats = {
            'dp_clauses_generated': 0,
            'dpll_recursive_calls': 0,
            'resolution_clauses_generated': 0
        }
        
        # DPLL
        print("1. DPLL")
        # Masurarea initiala
        mem_initial = self.get_memory_usage()
        cpu_initial = self.get_cpu_times()
        
        start = time.perf_counter()
        rezultat_dpll = self.dpll(clauze_dpll, set())
        end = time.perf_counter()
        
        # Masurarea finala
        mem_final = self.get_memory_usage()
        cpu_final = self.get_cpu_times()
        
        print(f"   Rezultat: {'Satisfiabila' if rezultat_dpll is not None else 'Nesatisfiabila'}")
        print(f"   Timp executie: {end - start:.6f} secunde")
        print(f"   Apeluri recursive: {self.stats['dpll_recursive_calls']}")
        print(f"   Memorie folosita: {mem_final - mem_initial:.2f} MB (peak: {mem_final:.2f} MB)")
        print(f"   CPU utilizat: {cpu_final - cpu_initial:.6f} secunde")
        
        # Davis-Putnam
        print("\n2. DAVIS-PUTNAM")
        # Masurarea initiala
        mem_initial = self.get_memory_usage()
        cpu_initial = self.get_cpu_times()
        
        start = time.perf_counter()
        rezultat_dp = self.algoritm_dp(clauze_dp)
        end = time.perf_counter()
        
        # Masurarea finala
        mem_final = self.get_memory_usage()
        cpu_final = self.get_cpu_times()
        
        print(f"   Rezultat: {'Satisfiabila' if rezultat_dp else 'Nesatisfiabila'}")
        print(f"   Timp executie: {end - start:.6f} secunde")
        print(f"   Clauze generate: {self.stats['dp_clauses_generated']}")
        print(f"   Memorie folosita: {mem_final - mem_initial:.2f} MB (peak: {mem_final:.2f} MB)")
        print(f"   CPU utilizat: {cpu_final - cpu_initial:.6f} secunde")
        
        # Rezolutie
        print("\n3. REZOLUȚIE")
        # Masurarea initiala
        mem_initial = self.get_memory_usage()
        cpu_initial = self.get_cpu_times()
        
        start = time.perf_counter()
        rezultat_resolution = self.rezolutie_sat(clauze_resolution)
        end = time.perf_counter()
        
        # Masurarea finala
        mem_final = self.get_memory_usage()
        cpu_final = self.get_cpu_times()
        
        if rezultat_resolution is not None:
            print(f"   Rezultat: {'Satisfiabila' if rezultat_resolution else 'Nesatisfiabila'}")
        else:
            print("   Rezultat: Timeout")
        print(f"   Timp executie: {end - start:.6f} secunde")
        print(f"   Clauze generate: {self.stats['resolution_clauses_generated']}")
        print(f"   Memorie folosita: {mem_final - mem_initial:.2f} MB (peak: {mem_final:.2f} MB)")
        print(f"   CPU utilizat: {cpu_final - cpu_initial:.6f} secunde")
        
        print("\n" + "=" * 80)
        print("SUMAR:")
        print(f"DPLL: {'SAT' if rezultat_dpll is not None else 'UNSAT'}")
        print(f"Davis-Putnam: {'SAT' if rezultat_dp else 'UNSAT'}")
        if rezultat_resolution is not None:
            print(f"Rezoluție: {'SAT' if rezultat_resolution else 'UNSAT'}")
        else:
            print("Rezoluție: TIMEOUT")

# Exemplu de utilizare
if __name__ == "__main__":
    solver = SATSolver()
    
    # Inlocuieste cu numele fișierului tau CNF
    nume_fisier = "teste/test8.cnf"
    
    try:
        solver.rezolva_toate(nume_fisier)
    except FileNotFoundError:
        print(f"Fișierul {nume_fisier} nu a fost găsit!")
        print("Înlocuiește 'test7.cnf' cu calea către fișierul tău CNF.")
    except ImportError:
        print("Biblioteca psutil nu este instalată!")
        print("Instalează cu: pip install psutil")
        print("Sau rulează programul fără metrici de sistem.")
