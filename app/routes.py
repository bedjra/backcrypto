from flask import Blueprint, request, jsonify
from app import db
from app.models import User
from app.models import Transaction , Fournisseur , Beneficiaire
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from datetime import datetime

main = Blueprint('main', __name__) 

##########################################################################################
##########################################################################################
@main.route('/save', methods=['POST'])
def save_user():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"message": "Email et mot de passe sont requis !"}), 400

    # Vérifier si l'utilisateur existe déjà
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"message": "Cet email est déjà utilisé !"}), 409

    # Hachage du mot de passe
    hashed_password = generate_password_hash(password)

    # Création et sauvegarde du nouvel utilisateur
    new_user = User(email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Utilisateur enregistré avec succès !"}), 201


####### utilisateur login ##################
@main.route('/login', methods=['POST'])
def login_user():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    # Trouver l'utilisateur par email
    user = User.query.filter_by(email=email).first()

    # Si l'utilisateur n'existe pas ou le mot de passe est incorrect
    if user and check_password_hash(user.password, password):
        return jsonify({"message": "Connexion réussie !"}), 200
    else:
        return jsonify({"message": "Email ou mot de passe incorrect !"}), 401


###############################################
#######  Get all utilisateur ##################
@main.route('/user', methods=['GET'])
def get_user():
    email = request.args.get('email')  # Récupère l'email passé en paramètre de requête
    
    # Trouver l'utilisateur par email
    user = User.query.filter_by(email=email).first()

    if user:
        # Si l'utilisateur existe, renvoyer ses informations
        return jsonify({
            "id": user.id,
            "email": user.email,
        }), 200
    else:
        # Si l'utilisateur n'existe pas
        return jsonify({"message": "Utilisateur non trouvé !"}), 404 







##########################################################################################
##########################################################################################
####### formulaire AJOUT TRANSACTION ##################
@main.route('/trans/add', methods=['POST'])
def ajouter_transaction():
    try:
        data = request.json
        print("📩 Données reçues:", data)

        montant_fcfa = float(data.get('montantFCFA', 0))
        taux_conv = float(data.get('tauxConv', 0))

        if montant_fcfa <= 0 or taux_conv <= 0:
            return jsonify({'message': 'Données invalides'}), 400

        montant_usdt = montant_fcfa / taux_conv

        transaction = Transaction(
            montant_FCFA=montant_fcfa,
            taux_convenu=taux_conv,
            montant_USDT=montant_usdt
            # Pas besoin de 'dateTransaction', c'est géré par SQLAlchemy
        )

        db.session.add(transaction)
        db.session.commit()

        return jsonify({
            'message': 'Transaction ajoutée',
            'transaction': {
                'montantFCFA': montant_fcfa,
                'tauxConv': taux_conv,
                'montantUSDT': montant_usdt,
                'dateTransaction': transaction.date_transaction.isoformat()

            }
        }), 201

    except Exception as e:
        print("🔥 Erreur serveur:", str(e))
        return jsonify({'message': 'Erreur interne', 'error': str(e)}), 500

####### get juste montant TRANSACTION ##################
@main.route('/trans/mont', methods=['GET'])
def get_transactions():
    try:
        transactions = Transaction.query.with_entities(Transaction.id, Transaction.montant_FCFA).order_by(Transaction.id.asc()).all()
        
        transactions_list = [{'id': t.id, 'montantFCFA': t.montant_FCFA} for t in transactions]

        return jsonify({'transactions': transactions_list}), 200

    except Exception as e:
        print("🔥 Erreur serveur:", str(e))
        return jsonify({'message': 'Erreur interne', 'error': str(e)}), 500

##############################################
#######  DELETE TRANSACTION ##################
@main.route('/trans/delete/<int:id>', methods=['DELETE'])
def delete_transaction(id):
    # Trouver la transaction par son ID
    transaction = Transaction.query.get(id)
    
    # Si la transaction n'existe pas
    if not transaction:
        return jsonify({"message": "Transaction non trouvée !"}), 404
    
    # Supprimer la transaction
    db.session.delete(transaction)
    db.session.commit()
    
    # Retourner un message de succès
    return jsonify({"message": "Transaction supprimée avec succès !"}), 200



##############################################
#######  Modifier TRANSACTION ################
@main.route('/trans/update/<int:id>', methods=['PUT'])
def update_transaction(id):
    # Trouver la transaction par son ID
    transaction = Transaction.query.get(id)

    # Si la transaction n'existe pas
    if not transaction:
        return jsonify({"message": "Transaction non trouvée !"}), 404
    
    # Récupérer les données envoyées en JSON
    data = request.json
    try:
        montant_fcfa = float(data.get('montantFCFA'))
        taux_conv = float(data.get('tauxConv'))
    except (TypeError, ValueError):
        return jsonify({'message': 'Données invalides, veuillez entrer des nombres'}), 400

    # Validation des données
    if montant_fcfa is None or taux_conv is None or taux_conv <= 0:
        return jsonify({'message': 'Données invalides'}), 400

    # Mettre à jour les champs de la transaction
    transaction.montant_FCFA = montant_fcfa
    transaction.taux_convenu = taux_conv
    transaction.montant_USDT = montant_fcfa / taux_conv  # Recalculer le montant en USDT
    transaction.date_transaction = db.func.current_timestamp()  # Mettre à jour la date de modification

    # Sauvegarder les modifications dans la base de données
    db.session.commit()

    # Retourner un message de succès avec les informations mises à jour
    return jsonify({
        "message": "Transaction mise à jour avec succès !",
        "transaction": {
            "id": transaction.id,
            "montantFCFA": transaction.montant_FCFA,
            "tauxConv": transaction.taux_convenu,
            "montantUSDT": transaction.montant_USDT,
            "dateTransaction": transaction.date_transaction
        }
    }), 200

###############################################
#######  Get all TRANSACTION ##################
@main.route('/trans/all', methods=['GET'])
def get_all_transactions():
    # Récupérer toutes les transactions triées par ID croissant
    transactions = Transaction.query.order_by(Transaction.id).all()

    # Si aucune transaction n'est trouvée
    if not transactions:
        return jsonify({"message": "Aucune transaction trouvée."}), 404
    
    # Formater les résultats pour les renvoyer
    transactions_list = [
        {
            "id": transaction.id,
            "montantFCFA": str(transaction.montant_FCFA),  # Convertir en string pour JSON
            "tauxConv": str(transaction.taux_convenu),
            "montantUSDT": str(transaction.montant_USDT),
            "dateTransaction": transaction.date_transaction.isoformat()  # Format ISO pour DateTime
        }
        for transaction in transactions
    ]
    
    # Retourner les transactions sous forme de JSON
    return jsonify({"transactions": transactions_list}), 200


###############################################
#######  Get 1 TRANSACTION ##################
@main.route('/trans/<int:id>', methods=['GET'])
def get_transaction_by_id(id):
    try:
        transaction = Transaction.query.get(id)

        if not transaction:
            return jsonify({'message': 'Transaction non trouvée'}), 404

        return jsonify({
            'id': transaction.id,
            'montantFCFA': transaction.montant_FCFA,
            'tauxConv': transaction.taux_convenu,
            'montantUSDT': transaction.montant_USDT,
            'dateTransaction': transaction.date_transaction.isoformat()
        }), 200

    except Exception as e:
        print("🔥 Erreur serveur:", str(e))
        return jsonify({'message': 'Erreur interne', 'error': str(e)}), 500

##########################################################################################
##########################################################################################
####### formulaire AJOUT Fournisseurs ##################
@main.route('/add/four', methods=['POST'])
def add_fournisseur():
    try:
        data = request.get_json()

        # Vérification des champs requis pour le fournisseur
        required_fields = ["nom", "taux_jour", "quantite_USDT", "transaction_id", "beneficiaires"]
        if not all(field in data for field in required_fields):
            return jsonify({"message": "Données incomplètes"}), 400

        # Récupération et validation des valeurs
        nom = data["nom"].strip()
        try:
            taux_jour = float(data["taux_jour"])
            quantite_USDT = float(data["quantite_USDT"])
        except ValueError:
            return jsonify({"message": "Taux du jour et quantité doivent être des nombres valides"}), 400

        transaction_id = data["transaction_id"]
        beneficiaires_data = data["beneficiaires"]

        # Vérification des valeurs positives
        if taux_jour <= 0 or quantite_USDT <= 0:
            return jsonify({"message": "Les valeurs du taux et de la quantité doivent être positives"}), 400

        # Vérifier si la transaction existe
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return jsonify({"message": "Transaction non trouvée"}), 404

        # Vérifier les bénéficiaires
        if not isinstance(beneficiaires_data, list) or len(beneficiaires_data) == 0:
            return jsonify({"message": "Au moins un bénéficiaire est requis"}), 400

        for benef in beneficiaires_data:
            if not all(k in benef for k in ["nom", "commission_USDT"]):
                return jsonify({"message": "Données du bénéficiaire incomplètes"}), 400
            if not isinstance(benef["nom"], str) or not benef["nom"].strip():
                return jsonify({"message": "Nom du bénéficiaire invalide"}), 400
            try:
                commission_USDT = float(benef["commission_USDT"])
                if commission_USDT < 0:
                    return jsonify({"message": "La commission doit être un nombre positif"}), 400
            except ValueError:
                return jsonify({"message": "Commission invalide"}), 400

        # Création du fournisseur
        new_fournisseur = Fournisseur(
            nom=nom,
            taux_jour=taux_jour,
            quantite_USDT=quantite_USDT,
            transaction_id=transaction_id
        )

        db.session.add(new_fournisseur)
        db.session.flush()  # Permet d'obtenir l'ID avant le commit

        # Création des bénéficiaires associés
        for benef in beneficiaires_data:
            new_benef = Beneficiaire(
                nom=benef["nom"].strip(),
                commission_USDT=float(benef["commission_USDT"]),
                fournisseur_id=new_fournisseur.id
            )
            db.session.add(new_benef)

        db.session.commit()  # Commit tout en une seule transaction

        return jsonify({
            "message": "Fournisseur et bénéficiaires ajoutés avec succès",
            "fournisseur": {
                "id": new_fournisseur.id,
                "nom": new_fournisseur.nom,
                "taux_jour": new_fournisseur.taux_jour,
                "quantite_USDT": new_fournisseur.quantite_USDT,
                "transaction_id": new_fournisseur.transaction_id,
                "beneficiaires": [
                    {"id": b.id, "nom": b.nom, "commission_USDT": b.commission_USDT}
                    for b in new_fournisseur.beneficiaires
                ]
            }
        }), 201

    except Exception as e:
        db.session.rollback()  # Annule tout si une erreur survient
        print("🔥 Erreur serveur:", str(e))
        return jsonify({"message": "Erreur lors de l'ajout", "error": str(e)}), 500

###############################################
#######  Get all FOURNISS ##################
@main.route('/all/four', methods=['GET'])
def get_all_fournisseurs():
    try:
        # Récupération des fournisseurs triés par leur ID réel
        fournisseurs = Fournisseur.query.order_by(Fournisseur.id).all()

        # Construction de la réponse
        result = []
        for fournisseur in fournisseurs:
            # Récupération des bénéficiaires associés
            beneficiaires = Beneficiaire.query.filter_by(fournisseur_id=fournisseur.id).all()

            result.append({
                "id": fournisseur.id,  # ID réel de la base de données
                "nom": fournisseur.nom,
                "taux_jour": float(fournisseur.taux_jour),
                "quantite_USDT": float(fournisseur.quantite_USDT),
                "transaction_id": fournisseur.transaction_id,
                "beneficiaires": [
                    {
                        "id": benef.id,
                        "nom": benef.nom,
                        "commission_USDT": float(benef.commission_USDT)
                    } for benef in beneficiaires
                ]
            })

        return jsonify({
            "message": "Liste des fournisseurs récupérée avec succès",
            "fournisseurs": result
        }), 200

    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération des fournisseurs", "error": str(e)}), 500


###############################################
#######  Get all fourn NOM ##################
@main.route('/all/four/nom', methods=['GET'])
def get_all_fournisseurs_noms():
    try:
        # Récupération des fournisseurs avec uniquement id et nom
        fournisseurs = Fournisseur.query.with_entities(Fournisseur.id, Fournisseur.nom).all()

        # Construction de la réponse
        result = [{"id": fournisseur.id, "nom": fournisseur.nom} for fournisseur in fournisseurs]

        return jsonify({
            "message": "Liste des noms des fournisseurs récupérée avec succès",
            "fournisseurs": result
        }), 200

    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération des noms des fournisseurs", "error": str(e)}), 500


############################################
#######  get by id ####################
@main.route('/four/<int:id>', methods=['GET'])
def get_fournisseur_by_id(id):
    try:
        # Récupération du fournisseur par ID
        fournisseur = Fournisseur.query.get(id)

        if not fournisseur:
            return jsonify({"message": f"Fournisseur avec l'ID {id} introuvable"}), 404

        # Récupération de la transaction associée au fournisseur
        transaction = fournisseur.transaction

        # Récupération des bénéficiaires associés au fournisseur
        beneficiaires = Beneficiaire.query.filter_by(fournisseur_id=fournisseur.id).all()

        # Construction de la réponse
        result = {
            "id": fournisseur.id,
            "nom": fournisseur.nom,
            "taux_jour": float(fournisseur.taux_jour),
            "quantite_USDT": float(fournisseur.quantite_USDT),
            "transaction_id": fournisseur.transaction_id,
            "transaction": {
                "id": transaction.id,
                "montant_FCFA": transaction.montant_FCFA,
                "taux_convenu": transaction.taux_convenu,
                "montant_USDT": float(transaction.montant_USDT),
            } if transaction else None,
            "beneficiaires": [
                {
                    "id": benef.id,
                    "nom": benef.nom,
                    "commission_USDT": float(benef.commission_USDT)
                } for benef in beneficiaires
            ]
        }

        return jsonify({
            "message": "Fournisseur récupéré avec succès",
            "fournisseur": result
        }), 200

    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération du fournisseur", "error": str(e)}), 500

    try:
        # Récupération du fournisseur par ID
        fournisseur = Fournisseur.query.get(id)

        if not fournisseur:
            return jsonify({"message": f"Fournisseur avec l'ID {id} introuvable"}), 404

        # Récupération des bénéficiaires associés au fournisseur
        beneficiaires = Beneficiaire.query.filter_by(fournisseur_id=fournisseur.id).all()

        # Construction de la réponse
        result = {
            "id": fournisseur.id,
            "nom": fournisseur.nom,
            "taux_jour": float(fournisseur.taux_jour),
            "quantite_USDT": float(fournisseur.quantite_USDT),
            "transaction_id": fournisseur.transaction_id,
           
            "beneficiaires": [
                {
                    "id": benef.id,
                    "nom": benef.nom,
                    "commission_USDT": float(benef.commission_USDT)
                } for benef in beneficiaires
            ]
        }

        return jsonify({
            "message": "Fournisseur récupéré avec succès",
            "fournisseur": result
        }), 200

    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération du fournisseur", "error": str(e)}), 500


###############################################
#######  put four ##################
@main.route('/update/four/<int:id>', methods=['PUT'])
def update_fournisseur(id):
    try:
        data = request.get_json()

        # Vérifier si le fournisseur existe
        fournisseur = Fournisseur.query.get(id)
        if not fournisseur:
            return jsonify({"message": "Fournisseur non trouvé"}), 404

        # Vérification des champs obligatoires
        required_fields = ["nom", "taux_jour", "quantite_USDT", "transaction_id", "beneficiaires"]
        if not all(field in data for field in required_fields):
            return jsonify({"message": "Données incomplètes"}), 400

        # Récupération et validation des valeurs
        nom = data["nom"].strip()
        try:
            taux_jour = float(data["taux_jour"])
            quantite_USDT = float(data["quantite_USDT"])
        except ValueError:
            return jsonify({"message": "Taux du jour et quantité doivent être des nombres valides"}), 400

        transaction_id = data["transaction_id"]
        beneficiaires_data = data["beneficiaires"]

        # Vérifier que les valeurs sont positives
        if taux_jour <= 0 or quantite_USDT <= 0:
            return jsonify({"message": "Les valeurs du taux et de la quantité doivent être positives"}), 400

        # Vérifier si la transaction existe
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return jsonify({"message": "Transaction non trouvée"}), 404

        # Vérifier les bénéficiaires
        if not isinstance(beneficiaires_data, list):
            return jsonify({"message": "Format invalide pour les bénéficiaires"}), 400

        for benef in beneficiaires_data:
            if not all(k in benef for k in ["nom", "commission_USDT"]):
                return jsonify({"message": "Données du bénéficiaire incomplètes"}), 400
            if not isinstance(benef["nom"], str) or not benef["nom"].strip():
                return jsonify({"message": "Nom du bénéficiaire invalide"}), 400
            try:
                commission_USDT = float(benef["commission_USDT"])
                if commission_USDT < 0:
                    return jsonify({"message": "La commission doit être un nombre positif"}), 400
            except ValueError:
                return jsonify({"message": "Commission invalide"}), 400

        # Mise à jour des informations du fournisseur
        fournisseur.nom = nom
        fournisseur.taux_jour = taux_jour
        fournisseur.quantite_USDT = quantite_USDT
        fournisseur.transaction_id = transaction_id

        # Supprimer les anciens bénéficiaires du fournisseur
        Beneficiaire.query.filter_by(fournisseur_id=id).delete()

        # Ajouter les nouveaux bénéficiaires
        for benef in beneficiaires_data:
            new_benef = Beneficiaire(
                nom=benef["nom"].strip(),
                commission_USDT=float(benef["commission_USDT"]),
                fournisseur_id=id
            )
            db.session.add(new_benef)

        db.session.commit()  # Commit tout en une seule transaction

        return jsonify({
            "message": "Fournisseur et bénéficiaires mis à jour avec succès",
            "fournisseur": {
                "id": fournisseur.id,
                "nom": fournisseur.nom,
                "taux_jour": fournisseur.taux_jour,
                "quantite_USDT": fournisseur.quantite_USDT,
                "transaction_id": fournisseur.transaction_id,
                "beneficiaires": [
                    {"id": b.id, "nom": b.nom, "commission_USDT": b.commission_USDT}
                    for b in fournisseur.beneficiaires
                ]
            }
        }), 200

    except Exception as e:
        db.session.rollback()  # Annule tout en cas d'erreur
        print("🔥 Erreur serveur:", str(e))
        return jsonify({"message": "Erreur lors de la mise à jour", "error": str(e)}), 500

##############################################
#######  DELETE FOUR ##################
@main.route('/delete/four/<int:id>', methods=['DELETE'])
def delete_fournisseur(id):
    fournisseur = Fournisseur.query.get(id)
    if not fournisseur:
        return jsonify({"message": "Fournisseur introuvable"}), 404

    db.session.delete(fournisseur)
    db.session.commit()
    return jsonify({"message": "Fournisseur supprimé avec succès"}), 200







########################################################################################    
##########################################################################################
##########################################################################################
############## DASHBORD ################## DASHBORD ##################
############## DASHBORD ################## DASHBORD ##################

#####################################################
#######  Get all four NUMBER TOTAL ##################
@main.route('/total/fr', methods=['GET'])
def get_total_fournisseurs():
    total_fournisseurs = Fournisseur.query.count()
    return jsonify({"total_fournisseurs": total_fournisseurs}), 200


#######################################################
#######  Get all transa NUMBER TOTAL ##################
@main.route('/total/tr', methods=['GET'])
def get_total_transactions():
    total_transactions = Transaction.query.count()  # Compter le nombre total de transactions
    return jsonify({"total": total_transactions}), 200

    
#######################################################
#######  Get all transa NUMBER TOTAL ##################
@main.route('/total/bn', methods=['GET'])
def get_total_beneficiaires():
    total_beneficiaires = Beneficiaire.query.count()
    return jsonify({"total_beneficiaires": total_beneficiaires}), 200







#######################################################################################
############## CALCUL ################## CALCUL ##################
############## CALCUL ################## CALCUL ##################
@main.route('/details/<int:transaction_id>', methods=['GET'])
def get_fournisseurs_par_transaction(transaction_id):
    try:
        # Vérifier si la transaction existe
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return jsonify({"message": "Transaction non trouvée"}), 404

        # Récupérer les fournisseurs liés à cette transaction
        fournisseurs = Fournisseur.query.filter_by(transaction_id=transaction_id).all()

        if not fournisseurs:
            return jsonify({"message": "Aucun fournisseur trouvé pour cette transaction"}), 404

        # Construire la réponse avec les bénéficiaires
        result = []
        for fournisseur in fournisseurs:
            result.append({
                "id": fournisseur.id,
                "nom": fournisseur.nom,
                "taux_jour": fournisseur.taux_jour,
                "quantite_USDT": fournisseur.quantite_USDT,
                "transaction_id": fournisseur.transaction_id,
                "beneficiaires": [
                    {"id": b.id, "nom": b.nom, "commission_USDT": b.commission_USDT}
                    for b in fournisseur.beneficiaires
                ]
            })

        return jsonify(result), 200

    except Exception as e:
        print("🔥 Erreur serveur:", str(e))
        return jsonify({"message": "Erreur lors de la récupération", "error": str(e)}), 500


@main.route("/cal/<int:transaction_id>", methods=["GET"])
def get_transaction_details(transaction_id):
    try:
        # Vérifier si la transaction existe
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return jsonify({"message": "Transaction non trouvée"}), 404

        # Récupérer les fournisseurs liés à cette transaction
        fournisseurs = Fournisseur.query.filter_by(transaction_id=transaction_id).all()
        if not fournisseurs:
            return jsonify({"message": "Aucun fournisseur trouvé pour cette transaction"}), 404

        # Calculs des bénéfices des fournisseurs
        total_benefice_fournisseurs = 0
        fournisseurs_list = []
        for fournisseur in fournisseurs:
            benefice_par_USDT = transaction.taux_convenu - fournisseur.taux_jour
            benefice_total = benefice_par_USDT * fournisseur.quantite_USDT
            total_benefice_fournisseurs += benefice_total

            fournisseurs_list.append({
                "fournisseur": fournisseur.nom,
                "benefice_par_USDT": benefice_par_USDT,
                "benefice_total_FCFA": benefice_total
            })

        # Calculs des bénéfices des bénéficiaires
        beneficiaires_list = {}
        for fournisseur in fournisseurs:
            for beneficiaire in fournisseur.beneficiaires:
                if beneficiaire.nom not in beneficiaires_list:
                    beneficiaires_list[beneficiaire.nom] = {
                        "commission_USDT": beneficiaire.commission_USDT,
                        "benefice_FCFA": 0
                    }
                
                benefice_beneficiaire = beneficiaire.commission_USDT * fournisseur.quantite_USDT
                beneficiaires_list[beneficiaire.nom]["benefice_FCFA"] += benefice_beneficiaire

        # Construire la réponse
        response = {
            "calculs_en_temps_reel": {
                "benefices_fournisseurs": fournisseurs_list,
                "repartition_beneficiaires": [
                    {
                        "beneficiaire": nom,
                        "commission_USDT": data["commission_USDT"],
                        "benefice_FCFA": data["benefice_FCFA"]
                    }
                    for nom, data in beneficiaires_list.items()
                ],
                "resume_global": {
                    "benefice_total_fournisseurs": total_benefice_fournisseurs,
                    "benefices_par_beneficiaire": beneficiaires_list
                }
            }
        }

        return jsonify(response), 200

    except Exception as e:
        print("🔥 Erreur serveur:", str(e))
        return jsonify({"message": "Erreur lors de la récupération", "error": str(e)}), 500

# 
# #########################################################################################    
##########################################################################################
##########################################################################################    
##########################################################################################
##########################################################################################
############## HISTORIQUE ################## HISTORIQUE ##################
############## HISTORIQUE ################## HISTORIQUE ##################
@main.route("/cal/all", methods=["GET"])
def get_alltransactions():
    try:
        transactions = Transaction.query.all()
        if not transactions:
            return jsonify({"message": "Aucune transaction trouvée"}), 404

        transactions_list = []
        for transaction in transactions:
            fournisseurs = Fournisseur.query.filter_by(transaction_id=transaction.id).all()
            fournisseurs_list = []
            beneficiaires_list = {}
            total_benefice_fournisseurs = 0

            for fournisseur in fournisseurs:
                benefice_par_USDT = transaction.taux_convenu - fournisseur.taux_jour
                benefice_total = benefice_par_USDT * fournisseur.quantite_USDT
                total_benefice_fournisseurs += benefice_total

                fournisseurs_list.append({
                    "fournisseur": fournisseur.nom,
                    "benefice_par_USDT": benefice_par_USDT,
                    "benefice_total_FCFA": benefice_total
                })

                for beneficiaire in fournisseur.beneficiaires:
                    benefice_beneficiaire = beneficiaire.commission_USDT * fournisseur.quantite_USDT
                    if beneficiaire.nom in beneficiaires_list:
                        beneficiaires_list[beneficiaire.nom] += benefice_beneficiaire
                    else:
                        beneficiaires_list[beneficiaire.nom] = benefice_beneficiaire

            transactions_list.append({
                "transaction_id": transaction.id,
                "taux_convenu": transaction.taux_convenu,
                "benefices_fournisseurs": fournisseurs_list,
                "repartition_beneficiaires": [
                    {"beneficiaire": nom, "benefice_FCFA": benefice}
                    for nom, benefice in beneficiaires_list.items()
                ],
                "resume_global": {
                    "benefice_total_fournisseurs": total_benefice_fournisseurs,
                    "benefices_par_beneficiaire": beneficiaires_list
                }
            })

        return jsonify({"transactions": transactions_list}), 200

    except Exception as e:
        print("🔥 Erreur serveur:", str(e))
        return jsonify({"message": "Erreur lors de la récupération", "error": str(e)}), 500
