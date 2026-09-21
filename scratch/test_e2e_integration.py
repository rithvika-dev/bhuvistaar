import json
import time
import urllib.request
import urllib.parse
import urllib.error

BASE_URL = "http://127.0.0.1:8001"

class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None

    def request(self, method, endpoint, data=None, json_data=None, files=None, headers=None, params=None):
        url = f"{self.base_url}{endpoint}"
        if params:
            url += "?" + urllib.parse.urlencode(params)

        req_headers = headers or {}
        if self.token:
            req_headers["Authorization"] = f"Bearer {self.token}"

        body = None
        if json_data is not None:
            body = json.dumps(json_data).encode("utf-8")
            req_headers["Content-Type"] = "application/json"
        elif data is not None and files is None:
            if isinstance(data, dict):
                body = urllib.parse.urlencode(data).encode("utf-8")
                req_headers["Content-Type"] = "application/x-www-form-urlencoded"
            else:
                body = data
        elif files is not None:
            boundary = f"----WebKitFormBoundary{int(time.time() * 1000)}"
            req_headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
            parts = []
            if data:
                for k, v in data.items():
                    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode("utf-8"))
            for field_name, (filename, content, content_type) in files.items():
                header = f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field_name}\"; filename=\"{filename}\"\r\nContent-Type: {content_type}\r\n\r\n"
                parts.append(header.encode("utf-8") + content.encode("utf-8") + b"\r\n")
            parts.append(f"--{boundary}--\r\n".encode("utf-8"))
            body = b"".join(parts)

        req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                resp_body = resp.read().decode("utf-8")
                status = resp.status
                try:
                    res_json = json.loads(resp_body)
                except Exception:
                    res_json = resp_body
                return status, res_json
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            try:
                err_json = json.loads(err_body)
            except Exception:
                err_json = err_body
            return e.code, err_json

def run_e2e_test():
    print("=" * 60)
    print("STARTING BHUVISTAAR END-TO-END INTEGRATION TEST")
    print("=" * 60)

    client = APIClient(BASE_URL)

    # 1. Auth Register & Login
    ts = int(time.time())
    test_user = {
        "name": f"E2E Officer {ts}",
        "email": f"e2e_test_{ts}@bhuvistaar.in",
        "password": "Password123!"
    }

    print("\n1. Registering user...")
    status, res = client.request("POST", "/auth/register", json_data=test_user)
    print(f"Register status: {status}, response: {res}")
    assert status in (200, 201), f"Register failed: {res}"

    print("\n2. Logging in...")
    login_payload = {
        "email": test_user["email"],
        "password": test_user["password"]
    }
    status, res = client.request("POST", "/auth/login", json_data=login_payload)
    print(f"Login status: {status}, response: {res}")
    assert status == 200, f"Login failed: {res}"
    client.token = res["access_token"]

    # 2. Create Project
    print("\n3. Creating project...")
    project_payload = {
        "name": "E2E Validation Project",
        "description": "End-to-End automated GIS integration test project",
        "state": "Maharashtra",
        "district": "Pune"
    }
    status, project = client.request("POST", "/projects/", json_data=project_payload)
    print(f"Project creation status: {status}, project: {project}")
    assert status in (200, 201), f"Project creation failed: {project}"
    project_id = project["id"]

    # 3. Upload Datasets
    cadastral_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "khasra_no": "101/A",
                    "owner_name": "Rajesh Sharma",
                    "area_sqm": 1250.5
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [73.8567, 18.5204],
                        [73.8577, 18.5204],
                        [73.8577, 18.5214],
                        [73.8567, 18.5214],
                        [73.8567, 18.5204]
                    ]]
                }
            }
        ]
    }

    drone_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "building_id": "DRONE-B101",
                    "owner": "Rajesh Sharma",
                    "footprint_area": 1245.0
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [73.8568, 18.52045],
                        [73.85775, 18.52045],
                        [73.85775, 18.52145],
                        [73.8568, 18.52145],
                        [73.8568, 18.52045]
                    ]]
                }
            }
        ]
    }

    print("\n4. Creating & Uploading Cadastral dataset...")
    ds1_meta = {
        "project_id": project_id,
        "name": "Cadastral Vector Layer",
        "dataset_type": "cadastral",
        "source": "Revenue Dept",
        "crs": "EPSG:4326",
        "description": "Cadastral boundaries"
    }
    status, ds1 = client.request("POST", "/datasets/", json_data=ds1_meta)
    print(f"Cadastral dataset meta creation: {status}, dataset: {ds1}")
    assert status in (200, 201), f"Cadastral dataset creation failed: {ds1}"
    ds1_id = ds1["id"]

    files1 = {
        "file": ("cadastral.geojson", json.dumps(cadastral_geojson), "application/json")
    }
    status, ds1_up = client.request("POST", f"/datasets/{ds1_id}/upload", files=files1)
    print(f"Cadastral file upload status: {status}, upload result: {ds1_up}")
    assert status in (200, 201), f"Cadastral upload failed: {ds1_up}"

    print("\n5. Creating & Uploading Drone dataset...")
    ds2_meta = {
        "project_id": project_id,
        "name": "Drone Survey Layer",
        "dataset_type": "drone",
        "source": "SVAMITVA Drone Unit",
        "crs": "EPSG:4326",
        "description": "Drone survey building footprints"
    }
    status, ds2 = client.request("POST", "/datasets/", json_data=ds2_meta)
    print(f"Drone dataset meta creation: {status}, dataset: {ds2}")
    assert status in (200, 201), f"Drone dataset creation failed: {ds2}"
    ds2_id = ds2["id"]

    files2 = {
        "file": ("drone_survey.geojson", json.dumps(drone_geojson), "application/json")
    }
    status, ds2_up = client.request("POST", f"/datasets/{ds2_id}/upload", files=files2)
    print(f"Drone file upload status: {status}, upload result: {ds2_up}")
    assert status in (200, 201), f"Drone upload failed: {ds2_up}"

    # 4. Vector Feature Processing
    print(f"\n6. Processing Vector Feature Extraction for Dataset {ds1_id}...")
    status, res = client.request("POST", f"/gis/datasets/{ds1_id}/process")
    print(f"Process ds1 status: {status}, output: {res}")
    assert status == 200, f"Process ds1 failed: {res}"

    print(f"\n7. Processing Vector Feature Extraction for Dataset {ds2_id}...")
    status, res = client.request("POST", f"/gis/datasets/{ds2_id}/process")
    print(f"Process ds2 status: {status}, output: {res}")
    assert status == 200, f"Process ds2 failed: {res}"

    # 5. AI Spatial Matching
    print(f"\n8. Running AI Spatial Matching for project {project_id}...")
    status, matching_result = client.request(
        "POST",
        "/matching/run",
        params={
            "project_id": project_id,
            "source_dataset_id": ds1_id,
            "target_dataset_id": ds2_id
        }
    )
    print(f"Matching status: {status}, output: {matching_result}")
    assert status == 200, f"Matching failed: {matching_result}"

    # Get matches
    status, res = client.request("GET", f"/match-results/{project_id}")
    print(f"Get matches status: {status}")
    matches = res.get("matches", []) if isinstance(res, dict) else []
    print(f"Total matches retrieved: {len(matches)}")

    if matches:
        match_id = matches[0]["id"]
        print(f"Reviewing match ID {match_id} as approved...")
        status, review_res = client.request("PUT", f"/match-results/{match_id}/review", json_data={
            "match_status": "approved",
            "review_notes": "Verified high overlap in test"
        })
        print(f"Match review status: {status}, response: {review_res}")
        assert status == 200

    # 6. Topology Validation
    print(f"\n9. Running Topology Validation for project {project_id}...")
    status, res = client.request("POST", "/topology/validate", params={
        "project_id": project_id,
        "dataset_id": ds1_id
    })
    print(f"Topology validation status: {status}, response: {res}")
    assert status == 200, f"Topology validation failed: {res}"

    # 7. Conflict Detection & Resolution
    print(f"\n10. Running Conflict Detection for project {project_id}...")
    status, res = client.request("POST", f"/conflicts/detect/{project_id}")
    print(f"Conflict detection status: {status}, response: {res}")
    assert status == 200, f"Conflict detection failed: {res}"

    # 8. Attribute Harmonization Mapping
    print(f"\n11. Suggesting Attribute Mappings...")
    status, res = client.request("POST", "/harmonization/suggest-mappings", json_data={
        "project_id": project_id,
        "source_dataset_id": ds1_id,
        "target_dataset_id": ds2_id,
        "source_fields": ["khasra_no", "owner_name", "area_sqm"],
        "target_fields": ["building_id", "owner", "footprint_area"]
    })
    print(f"Attribute mapping status: {status}, result: {res}")
    assert status == 200, f"Attribute mapping failed: {res}"

    # Get attribute mappings
    status, res = client.request("GET", f"/attribute-mappings/project/{project_id}")
    mappings = res.get("mappings", []) if isinstance(res, dict) else []
    print(f"Attribute mappings created: {len(mappings)}")

    # Approve mappings
    for m in mappings:
        status, res = client.request("PUT", f"/attribute-mappings/{m['id']}/resolve", json_data={
            "mapping_status": "approved",
            "notes": "Approved by E2E runner"
        })
        print(f"Approved attribute mapping {m['id']}: status {status}, response: {res}")
        assert status == 200

    # 9. Harmonized Feature Generation
    print(f"\n12. Generating Harmonized Features for project {project_id}...")
    status, gen_result = client.request("POST", f"/harmonized-features/generate/{project_id}")
    print(f"Harmonized feature generation status: {status}, output: {gen_result}")
    assert status == 200, f"Harmonized feature generation failed: {gen_result}"

    # Fetch harmonized features
    status, res = client.request("GET", f"/harmonized-features/{project_id}")
    print(f"Get harmonized features status: {status}")
    hf_list = res.get("features", []) if isinstance(res, dict) else []
    print(f"Retrieved harmonized features: {len(hf_list)}")

    if hf_list:
        hf_id = hf_list[0]["id"]
        print(f"Reviewing harmonized feature {hf_id}...")
        status, res = client.request("PUT", f"/harmonized-features/{hf_id}/review", json_data={
            "review_status": "approved",
            "review_notes": "E2E officer approval"
        })
        print(f"Harmonized feature review status: {status}, response: {res}")
        assert status == 200

    # 10. Audit Logs
    print(f"\n13. Fetching Audit Logs...")
    status, res = client.request("GET", f"/audit/{project_id}")
    print(f"Audit log status: {status}")
    logs = res.get("logs", []) if isinstance(res, dict) else []
    print(f"Retrieved audit log entries: {len(logs)}")
    assert len(logs) > 0

    # 11. Export Request
    print(f"\n14. Requesting Data Export...")
    status, res = client.request("POST", "/exports/", json_data={
        "project_id": project_id,
        "export_type": "harmonized_features",
        "format": "geojson"
    })
    print(f"Export request status: {status}, output: {res}")
    assert status in (200, 201), f"Export failed: {res}"

    print("\n" + "=" * 60)
    print("SUCCESS: ALL END-TO-END INTEGRATION STEPS PASSED 100%!")
    print("=" * 60)

if __name__ == "__main__":
    run_e2e_test()
