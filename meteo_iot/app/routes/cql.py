from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import get_session, EXEC_PROFILE_READ

router = APIRouter()

class CQLRequest(BaseModel):
    query: str

@router.post("/cql/", summary="Exécuter une requête CQL")
def executer_cql(req: CQLRequest):
    query = req.query.strip()
    if not query.lower().startswith(("select", "describe", "show")):
        raise HTTPException(
            status_code=403,
            detail="Seules les requêtes SELECT sont autorisées"
        )
    session, _ = get_session()
    try:
        rows = session.execute(query, execution_profile=EXEC_PROFILE_READ)
        colonnes = rows.column_names
        resultats = [dict(zip(colonnes, row)) for row in rows]
        for row in resultats:
            for k, v in row.items():
                if hasattr(v, 'isoformat'):
                    row[k] = v.isoformat()
                elif not isinstance(v, (str, int, float, bool, type(None))):
                    row[k] = str(v)
        return {
            "colonnes":  colonnes,
            "resultats": resultats,
            "nb_lignes": len(resultats)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))