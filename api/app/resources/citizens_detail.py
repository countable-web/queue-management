'''Copyright 2018 Province of British Columbia

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.'''

from flask import request, jsonify, g
from flask_restplus import Resource
import sqlalchemy.orm
from qsystem import api, db, oidc, socketio
from app.auth import required_scope
from app.models import Citizen, CSR, CitizenState
from cockroachdb.sqlalchemy import run_transaction
import logging
from marshmallow import ValidationError, pre_load
from app.schemas import CitizenSchema
from sqlalchemy import exc

@api.route("/citizens/<int:id>/", methods=["GET","PUT"])
class CitizenDetail(Resource):
    
    citizen_schema = CitizenSchema()

    #@oidc.accept_token(require_token=True)
    def get(self, id):
        try:
            #csr = CSR.query.filter_by(username=g.oidc_token_info['username']).first()
            csr = CSR.query.filter_by(username='adamkroon').first()
            citizen = Citizen.query.get(id)
            result = self.citizen_schema.dump(citizen)
            return {'citizen': result.data,
                    'errors': result.errors}

        except exc.SQLAlchemyError as e:
            print (e)
            return {'message': 'API is down'}, 500

    #@oidc.accept_token(require_token=True)
    def put(self, id):
        json_data = request.get_json()
        
        if not json_data:
            return {'message': 'No input data received for creating citizen'}, 400
        
        #csr = CSR.query.filter_by(username=g.oidc_token_info['username']).first()
        csr = CSR.query.filter_by(username='adamkroon').first()
        citizen = Citizen.query.get(id)
        
        try:
            citizen = self.citizen_schema.load(json_data, instance=citizen, partial=True).data

        except ValidationError as err:
            return {'message': err.messages}, 422

        db.session.add(citizen)
        db.session.commit()
        result = self.citizen_schema.dump(citizen)

        return {'citizen': result.data, 'errors': result.errors}, 200
