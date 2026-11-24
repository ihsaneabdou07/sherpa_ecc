from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional
import openpyxl
from openpyxl.chart import BarChart, LineChart, RadarChart, Reference, ScatterChart, Series
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


def build_native_excel_report(
    region: str,
    city: Optional[str],
    target_product: str,
    annual_production_tonnes: float,
    architectures: List[dict],
    sensitivity_curve: List[dict],
    pareto_others: List[dict],
    lang: str = "fr",
) -> BytesIO:
    is_en = lang == "en"
    display_loc = f"{city} ({region})" if city else region
    unit = architectures[0].get("unit", "MAD/L") if architectures else "MAD/L"

    wb = openpyxl.Workbook()

    # Styles communs
    thin = Side(style="thin", color="CBD5E1")
    border_all = Border(left=thin, right=thin, top=thin, bottom=thin)
    fill_green_dark = PatternFill("solid", fgColor="047857")
    fill_green_soft = PatternFill("solid", fgColor="ECFDF5")
    fill_slate_dark = PatternFill("solid", fgColor="1E293B")
    fill_slate_soft = PatternFill("solid", fgColor="F8FAFC")
    fill_section = PatternFill("solid", fgColor="E2E8F0")

    font_title = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    font_sub = Font(name="Calibri", size=10, italic=True, color="065F46")
    font_sec = Font(name="Calibri", size=11, bold=True, color="0F172A")
    font_th = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    font_td = Font(name="Calibri", size=10, color="0F172A")
    font_td_bold = Font(name="Calibri", size=10, bold=True, color="0F172A")

    # =========================================================================
    # ONGLET 1 : Synthèse & Architectures (BarCharts + RadarChart natifs)
    # =========================================================================
    ws1 = wb.active
    ws1.title = "Executive Summary" if is_en else "Synthèse & Architectures"
    ws1.views.sheetView[0].showGridLines = True
    ws1.freeze_panes = "A3"
    ws1.page_setup.orientation = ws1.ORIENTATION_LANDSCAPE
    ws1.page_setup.fitToWidth = 1
    ws1.page_setup.fitToHeight = 0
    ws1.sheet_properties.pageSetUpPr.fitToPage = True

    ws1.merge_cells("A1:M1")
    ws1["A1"] = (
        f"H2-MAROC DECISION STUDIO — TECHNO-ECONOMIC REPORT • {display_loc.upper()}"
        if is_en
        else f"H2-MAROC DECISION STUDIO — RAPPORT TECHNO-ÉCONOMIQUE • {display_loc.upper()}"
    )
    ws1["A1"].font = font_title
    ws1["A1"].fill = fill_green_dark
    ws1["A1"].alignment = Alignment(vertical="center", horizontal="left", indent=1)
    ws1.row_dimensions[1].height = 32

    ws1.merge_cells("A2:M2")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    ws1["A2"] = (
        f"SHERPA ECC Platform | Product: {target_product} | Target Capacity: {int(annual_production_tonnes):,} t/yr | Generated: {now_str}"
        if is_en
        else f"Plateforme SHERPA ECC | Produit : {target_product} | Capacité cible : {int(annual_production_tonnes):,} t/an | Généré le : {now_str}"
    )
    ws1["A2"].font = font_sub
    ws1["A2"].fill = fill_green_soft
    ws1["A2"].alignment = Alignment(vertical="center", horizontal="left", indent=1)
    ws1.row_dimensions[2].height = 22

    # Section 1 : Tableau comparatif (lignes 4 à 9)
    ws1.merge_cells("A4:M4")
    ws1["A4"] = (
        "1. RECOMMENDED ARCHITECTURES COMPARISON (DYNAMIC FORMULAS & MULTICRITERIA SCORES)"
        if is_en
        else "1. COMPARATIF DES ARCHITECTURES RECOMMANDÉES (FORMULES DYNAMIQUES & SCORES)"
    )
    ws1["A4"].font = font_sec
    ws1["A4"].fill = fill_section
    ws1.row_dimensions[4].height = 24

    headers1 = (
        [
            "Rank", "Architecture", "Unit Cost", "Unit", "Cost vs #1",
            "CO2 (kg/u)", "Water (L/u)", "Annual CO2 (t/yr)", "Annual Water (m³/yr)",
            "TRL", "Cost Score", "CO2 Score", "Water Score",
        ]
        if is_en
        else [
            "Rang", "Architecture", "Coût unitaire", "Unité", "Écart Coût vs #1",
            "CO2 (kg/u)", "Eau (L/u)", "CO2 Annuel (t/an)", "Eau Annuelle (m³/an)",
            "TRL", "Score Coût", "Score CO2", "Score Eau",
        ]
    )

    ws1.row_dimensions[5].height = 28
    for col_idx, h in enumerate(headers1, start=1):
        c = ws1.cell(row=5, column=col_idx, value=h)
        c.font = font_th
        c.fill = fill_slate_dark
        c.alignment = Alignment(vertical="center", horizontal="center", wrap_text=True)
        c.border = border_all

    badge_fills: Dict[int, tuple] = {
        1: (PatternFill("solid", fgColor="D1FAE5"), Font(name="Calibri", size=10, bold=True, color="065F46")),
        2: (PatternFill("solid", fgColor="DBEAFE"), Font(name="Calibri", size=10, bold=True, color="1E40AF")),
        3: (PatternFill("solid", fgColor="EDE9FE"), Font(name="Calibri", size=10, bold=True, color="5B21B6")),
    }

    for idx, arch in enumerate(architectures):
        r = 6 + idx
        ws1.row_dimensions[r].height = 24
        rank = int(arch.get("rank", idx + 1))
        radar = arch.get("radar", {})

        ws1.cell(row=r, column=1, value=f"#{rank}")
        ws1.cell(row=r, column=2, value=arch.get("badge", f"Arch {rank}"))
        ws1.cell(row=r, column=3, value=float(arch.get("cost", 0.0)))
        ws1.cell(row=r, column=4, value=arch.get("unit", unit))
        ws1.cell(row=r, column=5, value=f"=(C{r}-$C$6)/$C$6")
        ws1.cell(row=r, column=6, value=float(arch.get("co2", 0.0)))
        ws1.cell(row=r, column=7, value=float(arch.get("water", 0.0)))
        ws1.cell(row=r, column=8, value=f"=F{r}*{annual_production_tonnes}")
        ws1.cell(row=r, column=9, value=f"=G{r}*{annual_production_tonnes}")
        ws1.cell(row=r, column=10, value=arch.get("trl", ""))
        ws1.cell(row=r, column=11, value=float(radar.get("cost_score", 0.0)))
        ws1.cell(row=r, column=12, value=float(radar.get("co2_score", 0.0)))
        ws1.cell(row=r, column=13, value=float(radar.get("water_score", 0.0)))

        for col in range(1, 14):
            cell = ws1.cell(row=r, column=col)
            cell.border = border_all
            cell.alignment = Alignment(vertical="center", horizontal="left" if col == 2 else "center")
            if col <= 2 and rank in badge_fills:
                cell.fill, cell.font = badge_fills[rank]
            else:
                cell.font = font_td_bold if col == 3 else font_td
                if idx % 2 == 1:
                    cell.fill = fill_slate_soft

        ws1.cell(row=r, column=3).number_format = "0.00"
        ws1.cell(row=r, column=5).number_format = "+0.0%;-0.0%;0.0%"
        ws1.cell(row=r, column=6).number_format = "0.00"
        ws1.cell(row=r, column=7).number_format = "0.0"
        ws1.cell(row=r, column=8).number_format = "#,##0"
        ws1.cell(row=r, column=9).number_format = "#,##0"
        ws1.cell(row=r, column=11).number_format = "0.0"
        ws1.cell(row=r, column=12).number_format = "0.0"
        ws1.cell(row=r, column=13).number_format = "0.0"

    last_arch_row = 5 + len(architectures)
    sum_row = last_arch_row + 1
    ws1.row_dimensions[sum_row].height = 22
    ws1.cell(row=sum_row, column=2, value="Benchmark (Min / Avg)" if is_en else "Synthèse (Min / Moyenne)")
    ws1.cell(row=sum_row, column=3, value=f"=MIN(C6:C{last_arch_row})")
    ws1.cell(row=sum_row, column=6, value=f"=MIN(F6:F{last_arch_row})")
    ws1.cell(row=sum_row, column=7, value=f"=AVERAGE(G6:G{last_arch_row})")
    ws1.cell(row=sum_row, column=8, value=f"=MIN(H6:H{last_arch_row})")
    ws1.cell(row=sum_row, column=9, value=f"=AVERAGE(I6:I{last_arch_row})")
    ws1.cell(row=sum_row, column=11, value=f"=AVERAGE(K6:K{last_arch_row})")
    ws1.cell(row=sum_row, column=12, value=f"=AVERAGE(L6:L{last_arch_row})")
    ws1.cell(row=sum_row, column=13, value=f"=AVERAGE(M6:M{last_arch_row})")

    for col in range(1, 14):
        cell = ws1.cell(row=sum_row, column=col)
        cell.font = font_td_bold
        cell.fill = fill_section
        cell.border = border_all
        cell.alignment = Alignment(vertical="center", horizontal="left" if col == 2 else "center")

    ws1.cell(row=sum_row, column=3).number_format = "0.00"
    ws1.cell(row=sum_row, column=6).number_format = "0.00"
    ws1.cell(row=sum_row, column=7).number_format = "0.0"
    ws1.cell(row=sum_row, column=8).number_format = "#,##0"
    ws1.cell(row=sum_row, column=9).number_format = "#,##0"
    ws1.cell(row=sum_row, column=11).number_format = "0.0"
    ws1.cell(row=sum_row, column=12).number_format = "0.0"
    ws1.cell(row=sum_row, column=13).number_format = "0.0"

    # --- GRAPHIQUE NATIF 1 : BarChart Coût Unitaire ---
    chart_row = sum_row + 2
    if architectures:
        bar_cost = BarChart()
        bar_cost.type = "col"
        bar_cost.style = 10
        bar_cost.title = f"Unit Cost ({unit})" if is_en else f"Coût Unitaire ({unit})"
        bar_cost.y_axis.title = unit
        bar_cost.legend = None
        data_cost = Reference(ws1, min_col=3, min_row=5, max_row=last_arch_row)
        cats_arch = Reference(ws1, min_col=2, min_row=6, max_row=last_arch_row)
        bar_cost.add_data(data_cost, titles_from_data=True)
        bar_cost.set_categories(cats_arch)
        bar_cost.series[0].graphicalProperties.solidFill = "059669"
        bar_cost.width = 13
        bar_cost.height = 8.5
        ws1.add_chart(bar_cost, f"A{chart_row}")

        # --- GRAPHIQUE NATIF 2 : BarChart Émissions CO2 ---
        bar_co2 = BarChart()
        bar_co2.type = "col"
        bar_co2.style = 11
        bar_co2.title = "CO2 Intensity (kg CO2/u)" if is_en else "Intensité Carbone (kg CO2/u)"
        bar_co2.y_axis.title = "kg CO2 / unit"
        bar_co2.legend = None
        data_co2 = Reference(ws1, min_col=6, min_row=5, max_row=last_arch_row)
        bar_co2.add_data(data_co2, titles_from_data=True)
        bar_co2.set_categories(cats_arch)
        bar_co2.series[0].graphicalProperties.solidFill = "6366F1"
        bar_co2.width = 13
        bar_co2.height = 8.5
        ws1.add_chart(bar_co2, f"E{chart_row}")

        # --- GRAPHIQUE NATIF 3 : RadarChart Profil Multicritère ---
        radar_chart = RadarChart()
        radar_chart.type = "filled"
        radar_chart.style = 26
        radar_chart.title = "Multicriteria Profile (/100)" if is_en else "Profil Multicritère (/100)"
        data_radar = Reference(ws1, min_col=11, max_col=13, min_row=5, max_row=last_arch_row)
        radar_chart.add_data(data_radar, titles_from_data=True)
        radar_chart.set_categories(cats_arch)
        radar_chart.width = 13
        radar_chart.height = 8.5
        ws1.add_chart(radar_chart, f"I{chart_row}")

    # Tableau des hypothèses techniques sous les graphiques
    first_assumptions = architectures[0].get("assumptions") if architectures else None
    if isinstance(first_assumptions, dict) and first_assumptions:
        assump_start = chart_row + 18
        ws1.merge_cells(f"A{assump_start}:F{assump_start}")
        ws1[f"A{assump_start}"] = (
            "2. TECHNICAL SIMULATION ASSUMPTIONS"
            if is_en
            else "2. HYPOTHÈSES TECHNIQUES DE SIMULATION"
        )
        ws1[f"A{assump_start}"].font = font_sec
        ws1[f"A{assump_start}"].fill = fill_section
        ws1.row_dimensions[assump_start].height = 23

        for idx, (k, v) in enumerate(first_assumptions.items()):
            r = assump_start + 1 + idx
            ws1.row_dimensions[r].height = 19
            ws1.merge_cells(f"A{r}:C{r}")
            ws1.merge_cells(f"D{r}:F{r}")
            ws1.cell(row=r, column=1, value=str(k).replace("_", " ")).font = font_td_bold
            ws1.cell(row=r, column=1).fill = fill_slate_soft
            ws1.cell(row=r, column=4, value=v).font = font_td
            for c in range(1, 7):
                ws1.cell(row=r, column=c).border = border_all

    widths_1 = [9, 21, 13, 10, 15, 13, 13, 19, 20, 12, 13, 13, 13]
    for i, w in enumerate(widths_1, start=1):
        ws1.column_dimensions[get_column_letter(i)].width = w

    # =========================================================================
    # ONGLET 2 : Sensibilité FLH & Frontière de Pareto (LineChart + ScatterChart)
    # =========================================================================
    ws2 = wb.create_sheet("Sensitivity & Pareto" if is_en else "Sensibilité FLH & Pareto")
    ws2.views.sheetView[0].showGridLines = True
    ws2.freeze_panes = "A3"
    ws2.page_setup.orientation = ws2.ORIENTATION_LANDSCAPE
    ws2.page_setup.fitToWidth = 1
    ws2.page_setup.fitToHeight = 0
    ws2.sheet_properties.pageSetUpPr.fitToPage = True

    ws2.merge_cells("A1:K1")
    ws2["A1"] = (
        f"RENEWABLE SENSITIVITY (FLH) & PARETO FRONTIER — {display_loc.upper()}"
        if is_en
        else f"SENSIBILITÉ À LA DISPONIBILITÉ ENR (FLH) & FRONTIÈRE DE PARETO — {display_loc.upper()}"
    )
    ws2["A1"].font = font_title
    ws2["A1"].fill = fill_green_dark
    ws2["A1"].alignment = Alignment(vertical="center", horizontal="left", indent=1)
    ws2.row_dimensions[1].height = 30

    ws2.merge_cells("A2:K2")
    ws2["A2"] = (
        "Impact of +/-20% Full Load Hours (FLH) variation and Pareto cost-carbon trade-offs"
        if is_en
        else "Impact d'une variation de ±20 % des heures pleine charge EnR (FLH) et compromis Coût-CO2"
    )
    ws2["A2"].font = font_sub
    ws2["A2"].fill = fill_green_soft
    ws2["A2"].alignment = Alignment(vertical="center", horizontal="left", indent=1)
    ws2.row_dimensions[2].height = 22

    sens_headers = [
        "FLH (h/yr)" if is_en else "FLH (h/an)",
        "Variation",
        *[f"#{a.get('rank')} {a.get('badge')} ({unit})" for a in architectures],
        "Delta #1 vs +0%" if is_en else "Écart #1 vs Base",
    ]
    ws2.row_dimensions[4].height = 26
    for i, h in enumerate(sens_headers, start=1):
        c = ws2.cell(row=4, column=i, value=h)
        c.font = font_th
        c.fill = fill_slate_dark
        c.alignment = Alignment(vertical="center", horizontal="center", wrap_text=True)
        c.border = border_all

    base_row_excel = 7
    for idx, pt in enumerate(sensitivity_curve):
        if pt.get("label") == "+0%":
            base_row_excel = 5 + idx
            break

    for idx, pt in enumerate(sensitivity_curve):
        r = 5 + idx
        ws2.row_dimensions[r].height = 22
        is_base = pt.get("label") == "+0%"
        ws2.cell(row=r, column=1, value=pt.get("flh", 0))
        ws2.cell(row=r, column=2, value=pt.get("label", ""))
        for a_idx, arch in enumerate(architectures):
            c = ws2.cell(row=r, column=3 + a_idx, value=float(pt.get(arch.get("id", ""), 0.0)))
            c.number_format = "0.00"
        delta_col = 3 + len(architectures)
        dc = ws2.cell(row=r, column=delta_col, value=f"=(C{r}-$C${base_row_excel})/$C${base_row_excel}")
        dc.number_format = "+0.0%;-0.0%;0.0%"

        for col in range(1, delta_col + 1):
            cell = ws2.cell(row=r, column=col)
            cell.font = font_td_bold if is_base else font_td
            cell.alignment = Alignment(vertical="center", horizontal="center")
            cell.border = border_all
            if is_base:
                cell.fill = PatternFill("solid", fgColor="D1FAE5")

    # --- GRAPHIQUE NATIF 4 : LineChart Sensibilité FLH ---
    if sensitivity_curve and architectures:
        last_sens_row = 4 + len(sensitivity_curve)
        line_chart = LineChart()
        line_chart.style = 10
        line_chart.title = (
            f"Unit Cost Sensitivity to FLH ({unit})"
            if is_en
            else f"Sensibilité du Coût aux Heures EnR FLH ({unit})"
        )
        line_chart.y_axis.title = unit
        line_chart.x_axis.title = "FLH (h/an)"
        data_sens = Reference(ws2, min_col=3, max_col=2 + len(architectures), min_row=4, max_row=last_sens_row)
        cats_sens = Reference(ws2, min_col=1, min_row=5, max_row=last_sens_row)
        line_chart.add_data(data_sens, titles_from_data=True)
        line_chart.set_categories(cats_sens)

        series_colors = ["10B981", "2563EB", "7C3AED"]
        for s_idx, s in enumerate(line_chart.series):
            s.graphicalProperties.line.solidFill = series_colors[s_idx % len(series_colors)]
            s.graphicalProperties.line.width = 28000
            s.marker.symbol = "circle"
            s.marker.size = 6

        line_chart.width = 16
        line_chart.height = 9
        ws2.add_chart(line_chart, "G4")

    # Section Frontière de Pareto
    if pareto_others:
        p_start = 18
        ws2.merge_cells(f"A{p_start}:D{p_start}")
        ws2[f"A{p_start}"] = (
            "PARETO FRONTIER POINTS (COST VS CO2)"
            if is_en
            else "POINTS DE LA FRONTIÈRE DE PARETO (COÛT VS CO2)"
        )
        ws2[f"A{p_start}"].font = font_sec
        ws2[f"A{p_start}"].fill = fill_section
        ws2.row_dimensions[p_start].height = 23

        p_head = p_start + 1
        ws2.row_dimensions[p_head].height = 22
        p_cols = ["Config #", f"Cost ({unit})" if is_en else f"Coût ({unit})", "CO2 (kg/u)", "Profile" if is_en else "Profil"]
        for i, h in enumerate(p_cols, start=1):
            c = ws2.cell(row=p_head, column=i, value=h)
            c.font = font_th
            c.fill = fill_slate_dark
            c.alignment = Alignment(vertical="center", horizontal="center")
            c.border = border_all

        for idx, pt in enumerate(pareto_others):
            r = p_head + 1 + idx
            ws2.row_dimensions[r].height = 19
            ws2.cell(row=r, column=1, value=idx + 1)
            c_cost = ws2.cell(row=r, column=2, value=float(pt.get("cost", 0.0)))
            c_co2 = ws2.cell(row=r, column=3, value=float(pt.get("co2", 0.0)))
            ws2.cell(row=r, column=4, value="Pareto simulated" if is_en else "Simulé Pareto")
            c_cost.number_format = "0.00"
            c_co2.number_format = "0.00"
            for col in range(1, 5):
                cell = ws2.cell(row=r, column=col)
                cell.font = font_td
                cell.alignment = Alignment(vertical="center", horizontal="center")
                cell.border = border_all

        last_pareto_row = p_head + len(pareto_others)

        # --- GRAPHIQUE NATIF 5 : ScatterChart Frontière de Pareto ---
        scatter = ScatterChart()
        scatter.style = 10
        scatter.title = "Pareto Frontier (Cost vs CO2)" if is_en else "Frontière de Pareto (Coût vs CO2)"
        scatter.x_axis.title = f"Cost ({unit})" if is_en else f"Coût ({unit})"
        scatter.y_axis.title = "CO2 (kg/u)"
        xvalues = Reference(ws2, min_col=2, min_row=p_head + 1, max_row=last_pareto_row)
        yvalues = Reference(ws2, min_col=3, min_row=p_head + 1, max_row=last_pareto_row)
        series = Series(yvalues, xvalues, title="Pareto Frontier" if is_en else "Frontière de Pareto")
        series.marker.symbol = "circle"
        series.marker.size = 7
        series.marker.graphicalProperties.solidFill = "059669"
        series.graphicalProperties.line.noFill = True
        scatter.series.append(series)
        scatter.width = 16
        scatter.height = 9
        ws2.add_chart(scatter, f"G{p_start}")

    widths_2 = [14, 13, 21, 21, 21, 17, 15, 15, 15, 15, 15]
    for i, w in enumerate(widths_2, start=1):
        ws2.column_dimensions[get_column_letter(i)].width = w

    # =========================================================================
    # ONGLET 3 : Méthodologie & Notes
    # =========================================================================
    ws3 = wb.create_sheet("Methodology & Notes" if is_en else "Méthodologie & Notes")
    ws3.views.sheetView[0].showGridLines = True
    ws3.merge_cells("A1:F1")
    ws3["A1"] = (
        "METHODOLOGICAL FRAMEWORK — SHERPA ECC DECISION STUDIO"
        if is_en
        else "CADRE MÉTHODOLOGIQUE — STUDIO DÉCISIONNEL SHERPA ECC"
    )
    ws3["A1"].font = font_title
    ws3["A1"].fill = fill_slate_dark
    ws3["A1"].alignment = Alignment(vertical="center", horizontal="left", indent=1)
    ws3.row_dimensions[1].height = 30

    notes = (
        [
            ("1. Decision Axes", "Architectures are evaluated across 5 normalized criteria (0–100): Production Cost, Carbon Intensity, Water Footprint, Technological Readiness Level (TRL), and Effective Electrolyzer Efficiency."),
            ("2. Architecture Profiles", "#1 Best overall balances cost, carbon and water efficiency; #2 Lowest cost maximizes electrolyzer-to-RES ratio with lighter storage; #3 Lowest CO2 prioritizes deep decarbonization."),
            ("3. Carbon Boundary", "Total CO2 includes renewable electricity supply emissions and electrolyzer stack manufacturing, excluding downstream transport."),
            ("4. Water & Desalination", "In coastal and water-stressed Moroccan regions (Dakhla, Laâyoune, Safi, Jorf Lasfar), desalination energy demand is integrated into the regional profile."),
        ]
        if is_en
        else [
            ("1. Axes décisionnels", "Les architectures sont évaluées selon 5 critères normalisés (0–100) : Coût de production, Intensité carbone, Empreinte eau, Maturité technologique (TRL) et Efficacité effective de l'électrolyseur."),
            ("2. Profils d'architectures", "#1 Best overall équilibre coût, carbone et eau ; #2 Lowest cost maximise le ratio électrolyseur/EnR avec un stockage léger ; #3 Lowest CO2 privilégie la décarbonation maximale."),
            ("3. Périmètre Carbone (CO2)", "Le CO2 total intègre les émissions liées à l'électricité renouvelable et à la fabrication du stack de l'électrolyseur, hors transport aval."),
            ("4. Nexus Eau & Dessalement", "Pour les pôles côtiers et zones à stress hydrique (Dakhla, Laâyoune, Safi, Jorf Lasfar), la part de dessalement est intégrée au profil énergétique local."),
        ]
    )

    for idx, (title, desc) in enumerate(notes):
        r = 3 + idx * 2
        ws3.merge_cells(f"A{r}:B{r}")
        ws3.merge_cells(f"C{r}:F{r}")
        ws3.row_dimensions[r].height = 36
        ws3.cell(row=r, column=1, value=title).font = Font(name="Calibri", size=10.5, bold=True, color="047857")
        ws3.cell(row=r, column=1).fill = fill_green_soft
        ws3.cell(row=r, column=1).alignment = Alignment(vertical="center", horizontal="left", indent=1)
        ws3.cell(row=r, column=3, value=desc).font = font_td
        ws3.cell(row=r, column=3).alignment = Alignment(vertical="center", horizontal="left", wrap_text=True)
        for c in range(1, 7):
            ws3.cell(row=r, column=c).border = border_all

    for i, w in enumerate([18, 18, 24, 24, 24, 24], start=1):
        ws3.column_dimensions[get_column_letter(i)].width = w

    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    return stream