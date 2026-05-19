from flask import Flask, render_template, request

app = Flask(__name__)

RELATIONSHIPS = {
    'parent_child': {'label': 'Pai-Filho', 'phi': 0.25},
    'full_siblings': {'label': 'Irmãos completos', 'phi': 0.25},
    'half_siblings': {'label': 'Meio-irmãos', 'phi': 0.125},
    'first_cousins': {'label': 'Primos de 1º grau', 'phi': 0.0625},
    'unrelated': {'label': 'Não aparentados', 'phi': 0.0},
    'custom': {'label': 'Personalizado', 'phi': None},
}


def parse_phi(rel, custom_phi):
    if rel != 'custom':
        return RELATIONSHIPS.get(rel, {}).get('phi', 0.0)
    try:
        val = float(custom_phi)
        if val < 0:
            return 0.0
        return val
    except Exception:
        return 0.0


@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    steps = []
    if request.method == 'POST':
        calc = request.form.get('calculator', 'endogamia')

        if calc == 'endogamia':
            # Endogamia: accept either phi directly, or R, or choose relationship, or calculate by Wright
            rel = request.form.get('relationship')
            custom_phi = request.form.get('custom_phi', '').strip()
            custom_R = request.form.get('custom_R', '').strip()
            use_wright = request.form.get('use_wright') == 'on'

            if use_wright:
                # Wright inputs: generations from each individual to common ancestor and number of common ancestors
                try:
                    g1 = int(request.form.get('wright_g1', '1'))
                    g2 = int(request.form.get('wright_g2', '1'))
                    k = int(request.form.get('wright_k', '1'))
                    F_anc = float(request.form.get('wright_Fanc', '0') or 0)
                except Exception:
                    g1 = g2 = k = 1
                    F_anc = 0.0
                # Wright's coefficient of relationship R = sum_over_anc (1/2)^(g1+g2) * (1+F_anc)
                R = k * (0.5 ** (g1 + g2)) * (1 + F_anc)
                phi = R / 2
                steps.append(f"1) Calculado por método de Wright: k={k}, g1={g1}, g2={g2}, F(ancestral)={F_anc}")
                steps.append(f"2) R = k × (1/2)^(g1+g2) × (1+F_anc) = {R}")
                steps.append(f"3) φ = R / 2 = {phi}")

            else:
                # prefer explicit custom phi
                phi = parse_phi(rel, custom_phi)
                if phi == 0.0 and custom_R:
                    try:
                        R = float(custom_R)
                        phi = R / 2
                    except Exception:
                        R = 0.0
                else:
                    R = 2 * phi

                steps.append(f"1) Relação escolhida: {RELATIONSHIPS.get(rel, {}).get('label', rel)}")
                if custom_phi:
                    steps.append(f"2) Valor customizado informado para φ: {phi}")
                elif custom_R:
                    steps.append(f"2) Valor customizado informado para R: {R}")
                else:
                    steps.append(f"2) Usado valor padrão ou calculado: φ={phi} | R={R}")

                steps.append(f"3) Coeficiente de endogamia F = φ = {phi}")
                steps.append(f"4) Coeficiente de parentesco R = 2 × φ = {R}")

            result = {
                'calculator': 'Endogamia',
                'phi': phi,
                'F': phi,
                'R': R,
                'steps': steps,
            }

        elif calc == 'hardy':
            # Hardy-Weinberg: given p (allele A frequency), compute q = 1-p, expected genotype frequencies
            try:
                p = float(request.form.get('hw_p', '0.5'))
            except Exception:
                p = 0.5
            q = 1 - p
            p2 = p * p
            q2 = q * q
            pq2 = 2 * p * q
            steps.append(f"1) Frequência alélica p = {p}, q = {q}")
            steps.append(f"2) Genótipos esperados: p^2={p2}, 2pq={pq2}, q^2={q2}")
            result = {
                'calculator': 'Hardy-Weinberg',
                'p': p,
                'q': q,
                'p2': p2,
                'pq2': pq2,
                'q2': q2,
                'steps': steps,
            }

        elif calc == 'ne':
            # Effective population size: simple haploid/diploid formula options
            try:
                Nm = float(request.form.get('Nm', '0'))
                Nf = float(request.form.get('Nf', '0'))
                method = request.form.get('ne_method', 'sex_unequal')
            except Exception:
                Nm = Nf = 0.0
                method = 'sex_unequal'
            if method == 'sex_unequal' and Nm + Nf > 0:
                Ne = (4 * Nm * Nf) / (Nm + Nf)
                steps.append(f"1) Método sex-unequal: Nm={Nm}, Nf={Nf}")
                steps.append(f"2) Ne = 4*Nm*Nf/(Nm+Nf) = {Ne}")
            else:
                try:
                    N = float(request.form.get('N', '0'))
                except Exception:
                    N = 0.0
                Ne = N
                steps.append(f"1) Método simples: N={N} => Ne={Ne}")
            result = {'calculator': 'Ne', 'Ne': Ne, 'steps': steps}

        elif calc == 'hetero':
            try:
                p = float(request.form.get('het_p', '0.5'))
            except Exception:
                p = 0.5
            q = 1 - p
            He = 1 - (p * p + q * q)
            Ho = float(request.form.get('Ho', '') or 0)
            steps.append(f"1) p={p}, q={q}")
            steps.append(f"2) Heterozigosidade esperada He = 1 - (p^2+q^2) = {He}")
            if Ho:
                steps.append(f"3) Heterozigosidade observada Ho = {Ho}")
            result = {'calculator': 'Heterozigosidade', 'He': He, 'Ho': Ho, 'steps': steps}

    return render_template('index.html', relationships=RELATIONSHIPS, result=result)


if __name__ == '__main__':
    app.run(debug=True)
