# DELIVERY AGENTS.md

Controle de entregas de final de ano - kits, presentes e gestão de estoque para até 2500 participantes.

## delivery-setup

- python -c "from models import DeliveryItem, DeliveryLog; print('Delivery models ready')"
- python scripts/setup_delivery_categories.py
- python scripts/import_inventory.py
- mkdir -p static/delivery_reports

## delivery-inventory

- python scripts/load_inventory_excel.py --file=static/uploads/inventory.xlsx
- python -c "from app import app, db, DeliveryItem; app.app_context().push(); print(f'Inventory items: {DeliveryItem.query.count()}')"
- python scripts/validate_inventory_data.py
- python scripts/calculate_stock_levels.py

## delivery-categories

- python scripts/create_delivery_categories.py
- python -c "categories = ['Festa', 'Cesta Básica', 'Brinquedos', 'Material Escolar']; [print(f'- {cat}') for cat in categories]"
- python scripts/assign_items_to_categories.py

## delivery-checkin

- python -c "print('Delivery check-in available at: /delivery/checkin')"
- python scripts/validate_delivery_qr.py --code=SAMPLE123
- python scripts/update_delivery_status.py
- python scripts/check_delivery_conflicts.py

## delivery-control

- python scripts/track_deliveries.py --realtime
- python -c "from app import app, db, DeliveryLog; app.app_context().push(); delivered = DeliveryLog.query.filter_by(status='delivered').count(); print(f'Items delivered: {delivered}')"
- python scripts/check_stock_levels.py
- python scripts/alert_low_stock.py

## delivery-reports

- python scripts/generate_delivery_report.py --format=excel
- python scripts/pending_deliveries_report.py
- python scripts/stock_reconciliation.py
- python scripts/delivery_timeline.py

## delivery-reconcile

- python scripts/reconcile_inventory.py
- python scripts/identify_discrepancies.py
- python scripts/generate_final_report.py
- python -c "from datetime import datetime; print(f'Reconciliation completed at: {datetime.now().isoformat()}')"