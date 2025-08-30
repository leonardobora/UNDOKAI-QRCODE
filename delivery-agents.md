# DELIVERY AGENTS.md

Controle de entregas de final de ano - kits, presentes e gestão de estoque para até 2500 participantes.

## delivery-setup

- python -c "from models import DeliveryItem, DeliveryLog; print('Delivery models ready')"
- python -c "from utils import create_sample_delivery_items; create_sample_delivery_items(); print('Delivery categories configured')"
- mkdir -p static/delivery_reports
- python -c "print('Delivery system available at: /delivery and /inventory')"

## delivery-inventory

- python -c "from app import app, db; from models import DeliveryItem; app.app_context().push(); items = DeliveryItem.query.count(); print(f'Inventory items: {items}')"
- python -c "from app import app, db; from models import DeliveryItem; app.app_context().push(); categories = db.session.query(DeliveryItem.categoria).distinct().all(); print(f'Categories: {[c[0] for c in categories]}')"
- python -c "from app import app, db; from models import DeliveryItem; app.app_context().push(); total_stock = sum([item.estoque_atual for item in DeliveryItem.query.all()]); print(f'Total stock: {total_stock} items')"

## delivery-categories

- python -c "categories = ['Festa', 'Cesta Básica', 'Brinquedos', 'Material Escolar']; [print(f'- {cat}') for cat in categories]"
- python -c "from app import app, db; from models import DeliveryItem; app.app_context().push(); festa_items = DeliveryItem.query.filter_by(categoria='Festa').count(); print(f'Festa items: {festa_items}')"
- python -c "from app import app, db; from models import DeliveryItem; app.app_context().push(); cesta_items = DeliveryItem.query.filter_by(categoria='Cesta Básica').count(); print(f'Cesta Básica items: {cesta_items}')"

## delivery-checkin

- python -c "print('Delivery check-in available at: /delivery')"
- python -c "from app import app, db; from models import Participant; app.app_context().push(); sample_participant = Participant.query.first(); print(f'Sample QR for delivery: {sample_participant.qr_code if sample_participant else \"No participants yet\"}')"
- python -c "from models import DeliveryLog; print('Delivery tracking system ready')"

## delivery-control

- python -c "from app import app, db; from models import DeliveryLog; app.app_context().push(); delivered = DeliveryLog.query.filter_by(status='delivered').count(); print(f'Items delivered: {delivered}')"
- python -c "from app import app, db; from models import DeliveryItem; app.app_context().push(); low_stock = DeliveryItem.query.filter(DeliveryItem.estoque_atual <= 10).count(); print(f'Low stock items: {low_stock}')"
- python -c "from app import app, db; from models import DeliveryItem; app.app_context().push(); empty_stock = DeliveryItem.query.filter(DeliveryItem.estoque_atual == 0).count(); print(f'Empty stock items: {empty_stock}')"

## delivery-reports

- python -c "from app import app, db; from models import DeliveryLog, DeliveryItem, Participant; app.app_context().push(); deliveries = db.session.query(DeliveryLog, DeliveryItem, Participant).join(DeliveryItem).join(Participant).count(); print(f'Delivery transactions: {deliveries}')"
- python -c "from app import app, db; from models import DeliveryLog; app.app_context().push(); pending = DeliveryLog.query.filter_by(status='pending').count(); print(f'Pending deliveries: {pending}')"
- python -c "from datetime import datetime; print(f'Delivery reports generated at: {datetime.now().isoformat()}')"

## delivery-reconcile

- python -c "from app import app, db; from models import DeliveryItem; app.app_context().push(); items = DeliveryItem.query.all(); discrepancies = [item for item in items if item.estoque_inicial - item.items_delivered != item.estoque_atual]; print(f'Stock discrepancies found: {len(discrepancies)}')"
- python -c "from app import app, db; from models import DeliveryItem; app.app_context().push(); total_initial = sum([item.estoque_inicial for item in DeliveryItem.query.all()]); total_delivered = sum([item.items_delivered for item in DeliveryItem.query.all()]); print(f'Reconciliation: {total_initial} initial, {total_delivered} delivered')"
- python -c "from datetime import datetime; print(f'Reconciliation completed at: {datetime.now().isoformat()}')"
