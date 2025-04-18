from flask import Blueprint, request, jsonify, session
from app import db
from app.models import TransactionFournisseur, User
from app.models import Transaction , Fournisseur , Beneficiaire
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from sqlalchemy import desc
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta  # Ajout correct de timedelta
from decimal import Decimal
from flask_jwt_extended import jwt_required, get_jwt_identity



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
        access_token = create_access_token(identity=user.id, expires_delta=timedelta(hours=1))
        return jsonify({"message": "Connexion réussie !", "token": access_token}), 200
    else:
        return jsonify({"message": "Email ou mot de passe incorrect !"}), 401



###############################################
#######  Get all utilisateur ##################
@main.route('/user', methods=['GET'])
@jwt_required()
def get_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if user:
        return jsonify({
            "id": user.id,
            "email": user.email,
        }), 200
    else:
        return jsonify({"message": "Utilisateur non trouvé !"}), 404

###############################################
#######  info user ##################
@main.route('/user/connecte', methods=['GET'])
def get_current_user():
    try:
        user_id = session.get('user_id')  # Récupérer l'ID de l'utilisateur depuis la session
        if not user_id:
            return jsonify({"message": "Utilisateur non connecté"}), 401

        user = User.query.get(user_id)
        if not user:
            return jsonify({"message": "Utilisateur non trouvé"}), 404

        return jsonify({
            "Nom": getattr(user, 'nom', "Inconnu"),
            "Email": user.email,
            "Rôle": getattr(user, 'role', "Non défini"),
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

###############################################
#######  changer password ##################


@main.route('/change', methods=['POST'])
@jwt_required()
def change_password():
    
    print("🟢 Route /change appelée")

    try:
        data = request.get_json()
        print("📦 Données reçues :", data)

        email = get_jwt_identity()
        print("🔐 Identité du token :", email)

        old_password = data.get('old_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        if not old_password or not new_password or not confirm_password:
            return jsonify({"message": "Tous les champs sont requis !"}), 400

        if new_password != confirm_password:
            return jsonify({"message": "Les mots de passe ne correspondent pas !"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"message": "Utilisateur non trouvé !"}), 404

        if not check_password_hash(user.password, old_password):
            return jsonify({"message": "Ancien mot de passe incorrect !"}), 401

        user.password = generate_password_hash(new_password)
        db.session.commit()

        return jsonify({"message": "Mot de passe changé avec succès !"}), 200

    except Exception as e:
        print("❌ Erreur backend :", str(e))
        return jsonify({"message": "Erreur serveur", "error": str(e)}), 500


##########################################################################################
##########################################################################################
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

    
@main.route('/total/trs', methods=['GET'])
def gettotal_transactions():
    transactions = Transaction.query.with_entities(Transaction.id).all()  # Récupérer tous les IDs
    transaction_ids = [t.id for t in transactions]  # Extraire les IDs sous forme de liste
    
    return jsonify({"transactions": transaction_ids}), 200  # Retourner la liste des IDs

#######################################################
#######  Get all transa NUMBER TOTAL ##################
@main.route('/total/bn', methods=['GET'])
def get_total_beneficiaires():
    total_beneficiaires = Beneficiaire.query.count()
    return jsonify({"total_beneficiaires": total_beneficiaires}), 200





#######################################################
#######  Get all BENEFICE TOTAL ##################
@main.route('/total/been', methods=['GET'])
def gettotalbenefice():
    try:
        transactions = Transaction.query.all()
        if not transactions:
            return jsonify({"message": "Aucune transaction trouvée", "benefice_global_total": 0}), 404

        total_benefice = 0
        for transaction in transactions:
            fournisseurs = Fournisseur.query.filter_by(transaction_id=transaction.id).all()
            for fournisseur in fournisseurs:
                benefice_fournisseur = (transaction.taux_convenu - fournisseur.taux_jour) * fournisseur.quantite_USDT
                total_benefice += benefice_fournisseur

        return jsonify({"benefice_global_total": total_benefice}), 200

    except Exception as e:
        print("🔥 Erreur serveur:", str(e))
        return jsonify({"message": "Erreur lors de la récupération du bénéfice total", "error": str(e)}), 500



########################################################################################    
##########################################################################################
##########################################################################################
@main.route('/add/fourn', methods=['POST'])
def adddfournisseur():
    try:
        data = request.get_json()

        # Vérification des champs requis pour le fournisseur
        required_fields = ["nom", "taux_jour", "quantite_USDT", "beneficiaires"]
        if not all(field in data for field in required_fields):
            return jsonify({"message": "Données incomplètes"}), 400

        # Récupération et validation des valeurs
        nom = data["nom"].strip()
        try:
            taux_jour = float(data["taux_jour"])
            quantite_USDT = float(data["quantite_USDT"])
        except ValueError:
            return jsonify({"message": "Taux du jour et quantité doivent être des nombres valides"}), 400

        beneficiaires_data = data["beneficiaires"]

        # Vérification des valeurs positives
        if taux_jour <= 0 or quantite_USDT <= 0:
            return jsonify({"message": "Les valeurs du taux et de la quantité doivent être positives"}), 400

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
            quantite_USDT=quantite_USDT
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


@main.route('/update/fourn/<int:id>', methods=['PUT'])
def update_fournisseur(id):
    try:
        data = request.get_json()
        
        # Vérifier si le fournisseur existe
        fournisseur = Fournisseur.query.get(id)
        if not fournisseur:
            return jsonify({"message": "Fournisseur non trouvé"}), 404
        
        # Mise à jour des champs du fournisseur
        if "nom" in data:
            fournisseur.nom = data["nom"].strip()
        if "taux_jour" in data:
            try:
                taux_jour = float(data["taux_jour"])
                if taux_jour <= 0:
                    return jsonify({"message": "Le taux du jour doit être positif"}), 400
                fournisseur.taux_jour = taux_jour
            except ValueError:
                return jsonify({"message": "Taux du jour invalide"}), 400
        if "quantite_USDT" in data:
            try:
                quantite_USDT = float(data["quantite_USDT"])
                if quantite_USDT <= 0:
                    return jsonify({"message": "La quantité doit être positive"}), 400
                fournisseur.quantite_USDT = quantite_USDT
            except ValueError:
                return jsonify({"message": "Quantité USDT invalide"}), 400
        
        # Mise à jour des bénéficiaires
        if "beneficiaires" in data:
            beneficiaires_data = data["beneficiaires"]
            if not isinstance(beneficiaires_data, list) or len(beneficiaires_data) == 0:
                return jsonify({"message": "Au moins un bénéficiaire est requis"}), 400
            
            # Supprimer les anciens bénéficiaires
            Beneficiaire.query.filter_by(fournisseur_id=id).delete()
            
            # Ajouter les nouveaux bénéficiaires
            for benef in beneficiaires_data:
                if not all(k in benef for k in ["nom", "commission_USDT"]):
                    return jsonify({"message": "Données du bénéficiaire incomplètes"}), 400
                try:
                    commission_USDT = float(benef["commission_USDT"])
                    if commission_USDT < 0:
                        return jsonify({"message": "La commission doit être un nombre positif"}), 400
                except ValueError:
                    return jsonify({"message": "Commission invalide"}), 400
                
                new_benef = Beneficiaire(
                    nom=benef["nom"].strip(),
                    commission_USDT=commission_USDT,
                    fournisseur_id=fournisseur.id
                )
                db.session.add(new_benef)
        
        db.session.commit()
        
        return jsonify({
            "message": "Fournisseur mis à jour avec succès",
            "fournisseur": {
                "id": fournisseur.id,
                "nom": fournisseur.nom,
                "taux_jour": fournisseur.taux_jour,
                "quantite_USDT": fournisseur.quantite_USDT,
                "beneficiaires": [
                    {"id": b.id, "nom": b.nom, "commission_USDT": b.commission_USDT}
                    for b in fournisseur.beneficiaires
                ]
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        print("🔥 Erreur serveur:", str(e))
        return jsonify({"message": "Erreur lors de la mise à jour", "error": str(e)}), 500


@main.route('/delete/fourn/<int:id>', methods=['DELETE'])
def deletefournisseur(id):
    try:
        fournisseur = Fournisseur.query.get(id)
        if not fournisseur:
            return jsonify({"message": "Fournisseur non trouvé"}), 404

        # Supprimer les bénéficiaires liés à ce fournisseur
        Beneficiaire.query.filter_by(fournisseur_id=id).delete()

        # Supprimer le fournisseur
        db.session.delete(fournisseur)
        db.session.commit()

        return jsonify({"message": "Fournisseur supprimé avec succès"}), 200

    except Exception as e:
        db.session.rollback()
        print("🔥 Erreur serveur:", str(e))
        return jsonify({"message": "Erreur lors de la suppression", "error": str(e)}), 500


@main.route('/all/fourn', methods=['GET'])
def getallfournisseursssss():
    try:
        # Récupération de tous les fournisseurs triés par leur ID
        fournisseurs = Fournisseur.query.order_by(Fournisseur.id).all()

        # Construction de la réponse
        result = []
        for fournisseur in fournisseurs:
            result.append({
                "id": fournisseur.id,
                "nom": fournisseur.nom,
                "taux_jour": float(fournisseur.taux_jour),
                "quantite_USDT": float(fournisseur.quantite_USDT),
                "beneficiaires": [
                    {
                        "id": benef.id,
                        "nom": benef.nom,
                        "commission_USDT": float(benef.commission_USDT)
                    } for benef in fournisseur.beneficiaires
                ]
            })

        return jsonify({
            "message": "Liste des fournisseurs récupérée avec succès",
            "fournisseurs": result
        }), 200

    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération des fournisseurs", "error": str(e)}), 500



@main.route('/alll/ben', methods=['GET'])
def getall_beneficiaires():
    try:
        # Récupération de tous les bénéficiaires de tous les fournisseurs
        beneficiaires = Beneficiaire.query.all()

        # Construction de la réponse
        result = []
        for benef in beneficiaires:
            result.append({
                "id": benef.id,
                "nom": benef.nom,
                "commission_USDT": float(benef.commission_USDT)
            })

        return jsonify({
            "message": "Liste des bénéficiaires récupérée avec succès",
            "beneficiaires": result
        }), 200

    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération des bénéficiaires", "error": str(e)}), 500


##########################################################################################
##########################################################################################
####### formulaire AJOUT TRANSACTION ##################
@main.route('/trans/addd', methods=['POST'])
def ajoutetransaction():
    try:
        data = request.json
        print("📩 Données reçues:", data)

        montant_fcfa = float(data.get('montantFCFA', 0))
        taux_conv = float(data.get('tauxConv', 0))
        fournisseurs_ids = data.get('fournisseursIds', [])  # On récupère une liste vide si absent

        # Si "fournisseurId" est envoyé seul, on l'ajoute à la liste
        if not fournisseurs_ids and 'fournisseurId' in data:
         fournisseurs_ids = [data['fournisseurId']]

         # Liste des fournisseurs sélectionnés

        if montant_fcfa <= 0 or taux_conv <= 0:
            return jsonify({'message': 'Données invalides'}), 400

        if not fournisseurs_ids:
            return jsonify({'message': 'Aucun fournisseur sélectionné'}), 400

        # Vérifier l'existence des fournisseurs
        fournisseurs = Fournisseur.query.filter(Fournisseur.id.in_(fournisseurs_ids)).all()
        if len(fournisseurs) != len(fournisseurs_ids):
            return jsonify({'message': 'Un ou plusieurs fournisseurs sont introuvables'}), 404

        # Calcul du montant en USDT avec 3 décimales
        montant_usdt = round(montant_fcfa / taux_conv, 3)

        # Création de la transaction
        transaction = Transaction(
            montant_FCFA=montant_fcfa,
            taux_convenu=taux_conv,
            montant_USDT=montant_usdt
        )
        db.session.add(transaction)
        db.session.flush()  # Récupération de l'ID avant commit

        # Ajout dans la table intermédiaire
        for fournisseur in fournisseurs:
            transaction_fournisseur_entry = TransactionFournisseur(
                transaction_id=transaction.id,
                fournisseur_id=fournisseur.id
            )
            db.session.add(transaction_fournisseur_entry)

        db.session.commit()

        return jsonify({
            'message': 'Transaction ajoutée',
            'transaction': {
                'id': transaction.id,
                'montantFCFA': montant_fcfa,
                'tauxConv': taux_conv,
                'montantUSDT': montant_usdt,
                'dateTransaction': transaction.date_transaction.isoformat(),
                'fournisseurs': [{'id': f.id, 'nom': f.nom} for f in fournisseurs]
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        print("🔥 Erreur serveur:", str(e))
        return jsonify({'message': 'Erreur interne', 'error': str(e)}), 500

###############################################
#######  Get all TRANSACTION ##################
@main.route('/trans/alll', methods=['GET'])
def getAlltransactions():
    try:
        transactions = Transaction.query.all()
        result = []

        for transaction in transactions:
            fournisseurs = (
                db.session.query(Fournisseur)
                .join(TransactionFournisseur, Fournisseur.id == TransactionFournisseur.fournisseur_id)
                .filter(TransactionFournisseur.transaction_id == transaction.id)
                .all()
            )
            
            result.append({
                'id': transaction.id,
                'montantFCFA': transaction.montant_FCFA,
                'tauxConv': transaction.taux_convenu,
                'montantUSDT': transaction.montant_USDT,
                'dateTransaction': transaction.date_transaction.isoformat(),
                'fournisseurs': [{'id': f.id, 'nom': f.nom} for f in fournisseurs]
            })

        return jsonify(result), 200
    
    except Exception as e:
        print("🔥 Erreur serveur:", str(e))
        return jsonify({'message': 'Erreur interne', 'error': str(e)}), 500



@main.route('/tran/<int:transaction_id>', methods=['GET'])
def getTransactionById(transaction_id):
    try:
        transaction = Transaction.query.get(transaction_id)
        
        if not transaction:
            return jsonify({'message': 'Transaction non trouvée'}), 404
        
        fournisseurs = (
            db.session.query(Fournisseur)
            .join(TransactionFournisseur, Fournisseur.id == TransactionFournisseur.fournisseur_id)
            .filter(TransactionFournisseur.transaction_id == transaction.id)
            .all()
        )
        
        result = {
            'id': transaction.id,
            'montantFCFA': transaction.montant_FCFA,
            'tauxConv': transaction.taux_convenu,
            'montantUSDT': transaction.montant_USDT,
            'dateTransaction': transaction.date_transaction.isoformat(),
            'fournisseurs': [{
                'id': f.id,
                'nom': f.nom,
                'tauxJour': f.taux_jour,
                'quantiteUSDT': float(f.quantite_USDT),
                'beneficiaires': [{
                    'id': b.id,
                    'nom': b.nom,
                    'commissionUSDT': float(b.commission_USDT)
                } for b in f.beneficiaires]
            } for f in fournisseurs]
        }
        
        return jsonify(result), 200
    
    except Exception as e:
        print("🔥 Erreur serveur:", str(e))
        return jsonify({'message': 'Erreur interne', 'error': str(e)}), 500


@main.route('/trans/delete/<int:transaction_id>', methods=['DELETE'])
def supprimer_transaction(transaction_id):
    try:
        transaction = Transaction.query.get(transaction_id)
        
        if not transaction:
            return jsonify({'message': 'Transaction introuvable'}), 404

        # Supprimer les entrées associées dans la table intermédiaire
        TransactionFournisseur.query.filter_by(transaction_id=transaction_id).delete()

        # Supprimer la transaction elle-même
        db.session.delete(transaction)
        db.session.commit()

        return jsonify({'message': 'Transaction supprimée avec succès'}), 200

    except Exception as e:
        db.session.rollback()
        print("🔥 Erreur serveur:", str(e))
        return jsonify({'message': 'Erreur interne', 'error': str(e)}), 500



#######################################################################################
############## CALCUL ################## CALCUL ##################
############## CALCUL ################## CALCUL ##################



@main.route('/cal/<int:transaction_id>', methods=['GET'])
def calculertransaction(transaction_id):
    try:
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return jsonify({'message': 'Transaction non trouvée'}), 404

        # Récupérer les fournisseurs liés à cette transaction
        fournisseurs = (
            db.session.query(Fournisseur)
            .join(TransactionFournisseur, Fournisseur.id == TransactionFournisseur.fournisseur_id)
            .filter(TransactionFournisseur.transaction_id == transaction.id)
            .all()
        )

        if not fournisseurs:
            return jsonify({'message': 'Aucun fournisseur trouvé pour cette transaction'}), 404

        total_benefice_fournisseurs = Decimal(0)
        fournisseurs_list = []
        benefices_par_fournisseur = {}

        for fournisseur in fournisseurs:
            # Calcul du bénéfice spécifique à chaque fournisseur
            benefice_par_USDT = Decimal(transaction.taux_convenu) - Decimal(fournisseur.taux_jour)
            benefice_total = benefice_par_USDT * Decimal(fournisseur.quantite_USDT)
            total_benefice_fournisseurs += benefice_total

            # Stocker les informations du fournisseur
            fournisseurs_list.append({
                'fournisseur': fournisseur.nom,
                'benefice_par_USDT': str(benefice_par_USDT),
                'benefice_total_FCFA': str(benefice_total)
            })

            # Gestion des bénéficiaires
            beneficiaires_dict = {}

            for beneficiaire in fournisseur.beneficiaires:
                nom_beneficiaire = beneficiaire.nom
                commission_USDT = Decimal(beneficiaire.commission_USDT)
                
                # Calcul du bénéfice pour ce bénéficiaire
                benefice_beneficiaire = (benefice_total * commission_USDT) / Decimal(100)

                if nom_beneficiaire not in beneficiaires_dict:
                    beneficiaires_dict[nom_beneficiaire] = {
                        'commission_USDT': str(commission_USDT),
                        'benefice_FCFA': str(benefice_beneficiaire)
                    }
                else:
                    # Si le bénéficiaire est déjà là, on additionne les bénéfices
                    beneficiaires_dict[nom_beneficiaire]['benefice_FCFA'] = str(
                        Decimal(beneficiaires_dict[nom_beneficiaire]['benefice_FCFA']) + benefice_beneficiaire
                    )

            # Calcul du bénéfice restant pour ce fournisseur
            somme_benefices_beneficiaires = sum(Decimal(data['benefice_FCFA']) for data in beneficiaires_dict.values())
            benefice_restant = benefice_total - somme_benefices_beneficiaires

            benefices_par_fournisseur[fournisseur.nom] = {
                'benefices_par_beneficiaire': beneficiaires_dict,
                'benefice_restant': str(benefice_restant)
            }

        response = {
            'calculs_en_temps_reel': {
                'benefices_fournisseurs': fournisseurs_list,
                'details_par_fournisseur': benefices_par_fournisseur,
                'resume_global': {
                    'benefice_total_fournisseurs': str(total_benefice_fournisseurs)
                }
            }
        }

        return jsonify(response), 200

    except Exception as e:
        print("🔥 Erreur serveur:", str(e))
        return jsonify({'message': 'Erreur lors de la récupération', 'error': str(e)}), 500





@main.route('/call/<int:transaction_id>', methods=['GET'])
def calculer_transaction(transaction_id):
    try:
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return jsonify({'message': 'Transaction non trouvée'}), 404

        # Récupérer les fournisseurs liés à cette transaction
        fournisseurs = (
            db.session.query(Fournisseur)
            .join(TransactionFournisseur, Fournisseur.id == TransactionFournisseur.fournisseur_id)
            .filter(TransactionFournisseur.transaction_id == transaction.id)
            .all()
        )

        if not fournisseurs:
            return jsonify({'message': 'Aucun fournisseur trouvé pour cette transaction'}), 404

        total_benefice_fournisseurs = 0  # Stockage en entier
        fournisseurs_list = []
        benefices_par_fournisseur = {}

        for fournisseur in fournisseurs:
            # Calcul du bénéfice spécifique à chaque fournisseur
            benefice_par_USDT = int(Decimal(transaction.taux_convenu) - Decimal(fournisseur.taux_jour))
            benefice_total = int(benefice_par_USDT * Decimal(fournisseur.quantite_USDT))
            total_benefice_fournisseurs += benefice_total

            # Stocker les informations du fournisseur
            fournisseurs_list.append({
                'fournisseur': fournisseur.nom,
                'benefice_par_USDT': benefice_par_USDT,  # Stocké en entier
                'benefice_total_FCFA': benefice_total  # Stocké en entier
            })

            # Gestion des bénéficiaires
            beneficiaires_dict = {}

            for beneficiaire in fournisseur.beneficiaires:
                nom_beneficiaire = beneficiaire.nom
                commission_USDT = int(beneficiaire.commission_USDT)
                
                # Calcul du bénéfice pour ce bénéficiaire
                benefice_beneficiaire = int((benefice_total * commission_USDT) // 100)  # Division forcée en entier

                if nom_beneficiaire not in beneficiaires_dict:
                    beneficiaires_dict[nom_beneficiaire] = {
                        'commission_USDT': commission_USDT,
                        'benefice_FCFA': benefice_beneficiaire
                    }
                else:
                    # Si le bénéficiaire est déjà là, on additionne les bénéfices
                    beneficiaires_dict[nom_beneficiaire]['benefice_FCFA'] += benefice_beneficiaire

            # Calcul du bénéfice restant pour ce fournisseur
            somme_benefices_beneficiaires = sum(data['benefice_FCFA'] for data in beneficiaires_dict.values())
            benefice_restant = int(benefice_total - somme_benefices_beneficiaires)

            benefices_par_fournisseur[fournisseur.nom] = {
                'benefices_par_beneficiaire': beneficiaires_dict,
                'benefice_restant': benefice_restant
            }

        response = {
            'calculs_en_temps_reel': {
                'benefices_fournisseurs': fournisseurs_list,
                'details_par_fournisseur': benefices_par_fournisseur,
                'resume_global': {
                    'benefice_total_fournisseurs': total_benefice_fournisseurs  # Stocké en entier
                }
            }
        }

        return jsonify(response), 200

    except Exception as e:
        print("🔥 Erreur serveur:", str(e))
        return jsonify({'message': 'Erreur lors de la récupération', 'error': str(e)}), 500






#########################################################################################
############## HISTORIQUE ################## HISTORIQUE ##################
############## HISTORIQUE ################## HISTORIQUE ##################


@main.route("/cal/perid", methods=["GET"])
def get_all_transactions_periode():
    try:
        periode = request.args.get("periode")  # Paramètre pour filtrer (jour, semaine, mois, annee)
        
        # Date actuelle
        today = datetime.today().date()

        # Définir la date de début en fonction de la période
        if periode == "jour":
            start_date = today
        elif periode == "semaine":
            start_date = today - timedelta(weeks=1)  # 7 jours avant
        elif periode == "mois":
            start_date = today.replace(day=1)  # Début du mois
        elif periode == "annee":
            start_date = today.replace(month=1, day=1)  # Début de l'année
        else:
            start_date = None  # Pas de filtre spécifique

        # Récupération des transactions filtrées
        if start_date:
            transactions = Transaction.query.filter(Transaction.date_transaction >= start_date).order_by(Transaction.id.asc()).all()
        else:
            transactions = Transaction.query.order_by(Transaction.id.asc()).all()

        if not transactions:
            return jsonify({"message": "Aucune transaction trouvée"}), 404

        transactions_list = []

        for transaction in transactions:
            # Récupérer les fournisseurs liés à cette transaction
            fournisseurs = (
                db.session.query(Fournisseur)
                .join(TransactionFournisseur, Fournisseur.id == TransactionFournisseur.fournisseur_id)
                .filter(TransactionFournisseur.transaction_id == transaction.id)
                .all()
            )

            if not fournisseurs:
                continue  # Si aucun fournisseur, on passe à la transaction suivante

            total_benefice_fournisseurs = 0
            fournisseurs_list = []
            benefices_par_fournisseur = {}

            for fournisseur in fournisseurs:
                # Calcul du bénéfice spécifique à chaque fournisseur
                benefice_par_USDT = int(Decimal(transaction.taux_convenu) - Decimal(fournisseur.taux_jour))
                benefice_total = int(benefice_par_USDT * Decimal(fournisseur.quantite_USDT))
                total_benefice_fournisseurs += benefice_total

                # Stocker les informations du fournisseur
                fournisseurs_list.append({
                    'fournisseur': fournisseur.nom,
                    'benefice_par_USDT': benefice_par_USDT,
                    'benefice_total_FCFA': benefice_total
                })

                # Gestion des bénéficiaires
                beneficiaires_dict = {}

                for beneficiaire in fournisseur.beneficiaires:
                    nom_beneficiaire = beneficiaire.nom
                    commission_USDT = int(beneficiaire.commission_USDT)
                    
                    # Calcul du bénéfice pour ce bénéficiaire
                    benefice_beneficiaire = int((benefice_total * commission_USDT) // 100)

                    if nom_beneficiaire not in beneficiaires_dict:
                        beneficiaires_dict[nom_beneficiaire] = {
                            'commission_USDT': commission_USDT,
                            'benefice_FCFA': benefice_beneficiaire
                        }
                    else:
                        # Si le bénéficiaire est déjà là, on additionne les bénéfices
                        beneficiaires_dict[nom_beneficiaire]['benefice_FCFA'] += benefice_beneficiaire

                # Calcul du bénéfice restant pour ce fournisseur
                somme_benefices_beneficiaires = sum(data['benefice_FCFA'] for data in beneficiaires_dict.values())
                benefice_restant = int(benefice_total - somme_benefices_beneficiaires)

                benefices_par_fournisseur[fournisseur.nom] = {
                    'benefices_par_beneficiaire': beneficiaires_dict,
                    'benefice_restant': benefice_restant
                }

            # Ajouter les informations de la transaction
            transactions_list.append({
                "transaction_id": transaction.id,
                "date_transaction": transaction.date_transaction.strftime("%Y-%m-%d"),
                "taux_convenu": transaction.taux_convenu,
                "montant_FCFA": transaction.montant_FCFA,
                "montant_USDT": int(transaction.montant_USDT),  
                "benefices_fournisseurs": fournisseurs_list,
                "details_par_fournisseur": benefices_par_fournisseur,
                "resume_global": {
                    "benefice_total_fournisseurs": total_benefice_fournisseurs
                }
            })

        return jsonify({"transactions": transactions_list}), 200

    except Exception as e:
        print("🔥 Erreur serveur:", str(e))
        return jsonify({"message": "Erreur lors de la récupération", "error": str(e)}), 500




@main.route("/accc/last", methods=["GET"])
def get_all_transactions():
    try:
        # Récupérer les 3 dernières transactions triées par date décroissante
        transactions = Transaction.query.order_by(Transaction.date_transaction.desc()).limit(3).all()

        if not transactions:
            return jsonify({"message": "Aucune transaction trouvée"}), 404

        transactions_list = []

        for transaction in transactions:
            # Récupérer les fournisseurs liés à cette transaction
            fournisseurs = (
                db.session.query(Fournisseur)
                .join(TransactionFournisseur, Fournisseur.id == TransactionFournisseur.fournisseur_id)
                .filter(TransactionFournisseur.transaction_id == transaction.id)
                .all()
            )

            if not fournisseurs:
                continue  # Si aucun fournisseur, on passe à la transaction suivante

            total_benefice_fournisseurs = 0
            fournisseurs_list = []

            for fournisseur in fournisseurs:
                # Calcul du bénéfice spécifique à chaque fournisseur
                benefice_par_USDT = int(Decimal(transaction.taux_convenu) - Decimal(fournisseur.taux_jour))
                benefice_total = int(benefice_par_USDT * Decimal(fournisseur.quantite_USDT))
                total_benefice_fournisseurs += benefice_total

                # Stocker les informations du fournisseur
                fournisseurs_list.append({
                    'fournisseur': fournisseur.nom,
                    'benefice_total_FCFA': benefice_total
                })

            # Ajouter les informations de la transaction au format demandé
            transactions_list.append({
                "date_transaction": transaction.date_transaction.strftime("%Y-%m-%d"),
                "montant_FCFA": transaction.montant_FCFA,
                "fournisseur": ", ".join([fournisseur['fournisseur'] for fournisseur in fournisseurs_list]),
                "benefice_total_FCFA": total_benefice_fournisseurs
            })

        return jsonify({"transactions": transactions_list}), 200

    except Exception as e:
        print("🔥 Erreur serveur:", str(e))
        return jsonify({"message": "Erreur lors de la récupération", "error": str(e)}), 500
