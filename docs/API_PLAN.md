# API inicial recomendada

## Auth
POST `/api/accounts/token/`
POST `/api/accounts/token/refresh/`

## Instituciones
GET/POST `/api/institutions/`
GET/PUT/PATCH `/api/institutions/{id}/`
GET/POST `/api/institutions/{id}/careers/`
GET/POST `/api/institutions/{id}/periods/`

## Empresas
GET/POST `/api/companies/`
POST `/api/companies/{id}/validate/`
GET/POST `/api/companies/{id}/supervisors/`

## Oportunidades
GET/POST `/api/internships/opportunities/`
GET/PUT/PATCH `/api/internships/opportunities/{id}/`

## Postulaciones
GET/POST `/api/internships/applications/`
POST `/api/internships/applications/{id}/accept/`
POST `/api/internships/applications/{id}/reject/`

## Pasantías
GET `/api/internships/internships/`
POST `/api/internships/internships/{id}/activities/`
POST `/api/internships/activities/{id}/validate/`
POST `/api/internships/internships/{id}/evaluate/`
GET `/api/internships/internships/{id}/certificate/`

## Dashboard
GET `/api/internships/dashboard/`

La implementación de ViewSets/Serializers puede agregarse sobre estos modelos.
