from sqlalchemy.orm import Session

from app.modules.catalog.service import import_catalog_csv


def _row(
    name: str,
    brand: str,
    category: str,
    routine_step: str,
    periods: str,
    price: str,
    formula: str,
    tags: str,
) -> str:
    return f'"{name}","{brand}","{category}","{routine_step}","{periods}","{price}","{formula}","{tags}","seed"'


def seed_catalog_products(db: Session) -> None:
    rows = [
        "name,brand,category,routine_step,usage_periods,price_range,raw_ingredient_list,tags,source",
    ]

    cleansers = [
        ("Gel Limpeza Suave 01", "DermaLab", "Aqua, Glycerin, Cocamidopropyl Betaine, Sodium Cocoyl Glutamate, Panthenol"),
        ("Espuma Balance 02", "ClaraSkin", "Aqua, Decyl Glucoside, Glycerin, Niacinamide, Allantoin"),
        ("Gel Oleosidade 03", "BioFace", "Aqua, Cocamidopropyl Betaine, Zinc PCA, Glycerin, Salicylic Acid"),
        ("Cleanser Barreira 04", "SkinBase", "Aqua, Sodium Lauroyl Sarcosinate, Glycerin, Ceramide NP, Panthenol"),
        ("Gel Calmante 05", "NudeCare", "Aqua, Decyl Glucoside, Aloe Barbadensis Leaf Juice, Glycerin, Allantoin"),
        ("Limpeza Hidratante 06", "Lumi", "Aqua, Glycerin, Sodium Cocoyl Isethionate, Betaine, Panthenol"),
        ("Gel Antiacne 07", "AcneLab", "Aqua, Cocamidopropyl Betaine, Salicylic Acid, Niacinamide, Zinc PCA"),
        ("Cleanser Minimal 08", "PureForm", "Aqua, Glycerin, Decyl Glucoside, Sodium Chloride, Citric Acid"),
        ("Gel Pele Sensivel 09", "SensiDerm", "Aqua, Glycerin, Coco-Glucoside, Allantoin, Panthenol"),
        ("Espuma Purificante 10", "MossLab", "Aqua, Sodium Cocoyl Glutamate, Glycerin, Green Tea Extract, Zinc PCA"),
    ]
    moisturizers = [
        ("Hidratante Gel 01", "DermaLab", "Aqua, Glycerin, Niacinamide, Hyaluronic Acid, Panthenol"),
        ("Creme Barreira 02", "ClaraSkin", "Aqua, Glycerin, Ceramide NP, Cholesterol, Fatty Acids"),
        ("Loção Calmante 03", "BioFace", "Aqua, Squalane, Glycerin, Allantoin, Panthenol"),
        ("Gel Oil Free 04", "SkinBase", "Aqua, Dimethicone, Glycerin, Niacinamide, Zinc PCA"),
        ("Creme Reparador 05", "NudeCare", "Aqua, Shea Butter, Ceramide NP, Panthenol, Glycerin"),
        ("Gel Hidra 06", "Lumi", "Aqua, Hyaluronic Acid, Glycerin, Betaine, Allantoin"),
        ("Hidratante Acne Safe 07", "AcneLab", "Aqua, Glycerin, Niacinamide, Panthenol, Zinc PCA"),
        ("Creme Minimal 08", "PureForm", "Aqua, Glycerin, Caprylic Triglyceride, Ceramide NP, Tocopherol"),
        ("Calm Balm 09", "SensiDerm", "Aqua, Panthenol, Glycerin, Madecassoside, Ceramide NP"),
        ("Moisture Cloud 10", "MossLab", "Aqua, Glycerin, Squalane, Hyaluronic Acid, Green Tea Extract"),
    ]
    sunscreens = [
        ("Protetor Solar FPS50 01", "DermaLab", "Aqua, Zinc Oxide, Glycerin, Niacinamide, Tocopherol"),
        ("Sunscreen Oil Control 02", "ClaraSkin", "Aqua, UV Filter, Silica, Niacinamide, Glycerin"),
        ("Protetor Mineral 03", "BioFace", "Aqua, Zinc Oxide, Titanium Dioxide, Glycerin, Panthenol"),
        ("SPF Gel 04", "SkinBase", "Aqua, UV Filter, Dimethicone, Glycerin, Zinc PCA"),
        ("Protetor Sensivel 05", "NudeCare", "Aqua, Zinc Oxide, Panthenol, Allantoin, Glycerin"),
        ("FPS Hidra 06", "Lumi", "Aqua, UV Filter, Hyaluronic Acid, Glycerin, Tocopherol"),
        ("Acne SPF 07", "AcneLab", "Aqua, UV Filter, Niacinamide, Zinc PCA, Glycerin"),
        ("Mineral Daily 08", "PureForm", "Aqua, Zinc Oxide, Squalane, Glycerin, Tocopherol"),
        ("Sensi SPF 09", "SensiDerm", "Aqua, Titanium Dioxide, Zinc Oxide, Panthenol, Allantoin"),
        ("Urban SPF 10", "MossLab", "Aqua, UV Filter, Green Tea Extract, Glycerin, Niacinamide"),
    ]
    acne_treatments = [
        ("Tratamento Acne 01", "DermaLab", "Aqua, Salicylic Acid, Niacinamide, Glycerin, Zinc PCA"),
        ("Serum Azelaico 02", "ClaraSkin", "Aqua, Azelaic Acid, Niacinamide, Panthenol, Glycerin"),
        ("Gel BHA 03", "BioFace", "Aqua, Salicylic Acid, Green Tea Extract, Glycerin, Allantoin"),
        ("Serum Oleosidade 04", "SkinBase", "Aqua, Niacinamide, Zinc PCA, Panthenol, Glycerin"),
        ("Tratamento Pontual 05", "NudeCare", "Aqua, Benzoyl Peroxide, Glycerin, Allantoin, Panthenol"),
        ("Acne Calm 06", "Lumi", "Aqua, Niacinamide, Azelaic Acid, Glycerin, Madecassoside"),
        ("Serum Poros 07", "AcneLab", "Aqua, Salicylic Acid, Niacinamide, Zinc PCA, Hyaluronic Acid"),
        ("Gel Renovador 08", "PureForm", "Aqua, Lactic Acid, Niacinamide, Glycerin, Panthenol"),
        ("Serum Controle 09", "SensiDerm", "Aqua, Niacinamide, Panthenol, Zinc PCA, Allantoin"),
        ("BHA Balance 10", "MossLab", "Aqua, Salicylic Acid, Green Tea Extract, Niacinamide, Glycerin"),
    ]
    barriers = [
        ("Reparo Barreira 01", "DermaLab", "Aqua, Ceramide NP, Cholesterol, Fatty Acids, Glycerin"),
        ("Serum Panthenol 02", "ClaraSkin", "Aqua, Panthenol, Glycerin, Madecassoside, Allantoin"),
        ("Creme Cica 03", "BioFace", "Aqua, Madecassoside, Ceramide NP, Glycerin, Squalane"),
        ("Barrier Serum 04", "SkinBase", "Aqua, Ceramide NP, Niacinamide, Panthenol, Hyaluronic Acid"),
        ("Balm Reparador 05", "NudeCare", "Aqua, Shea Butter, Ceramide NP, Cholesterol, Panthenol"),
        ("Hidra Barreira 06", "Lumi", "Aqua, Glycerin, Panthenol, Betaine, Ceramide NP"),
        ("Calm Repair 07", "AcneLab", "Aqua, Allantoin, Panthenol, Glycerin, Madecassoside"),
        ("Creme Ceramidas 08", "PureForm", "Aqua, Ceramide NP, Ceramide AP, Cholesterol, Glycerin"),
        ("Sensi Rebuild 09", "SensiDerm", "Aqua, Panthenol, Ceramide NP, Allantoin, Squalane"),
        ("Barrier Light 10", "MossLab", "Aqua, Niacinamide, Ceramide NP, Green Tea Extract, Glycerin"),
    ]

    for name, brand, formula in cleansers:
        rows.append(_row(name, brand, "cleanser", "cleanser", "morning;night", "mid", formula, "cleanser;gentle"))
    for name, brand, formula in moisturizers:
        rows.append(_row(name, brand, "moisturizer", "moisturizer", "morning;night", "mid", formula, "moisturizer;hydration"))
    for name, brand, formula in sunscreens:
        rows.append(_row(name, brand, "sunscreen", "sunscreen", "morning", "mid", formula, "sunscreen;spf"))
    for name, brand, formula in acne_treatments:
        rows.append(_row(name, brand, "acne_treatment", "treatment", "night", "mid", formula, "active;acne;treatment"))
    for name, brand, formula in barriers:
        rows.append(_row(name, brand, "barrier_repair", "moisturizer", "night", "mid", formula, "barrier_repair;moisturizer"))

    import_catalog_csv(db, "\n".join(rows), generate_external_embeddings=False)
