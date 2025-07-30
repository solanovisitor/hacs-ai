"""
HACS Database Migrations (Async)

Asynchronous migration runner that creates the necessary database schema
for HACS using psycopg (v3) for non-blocking operations.
"""

import asyncio
import logging
import os
import sys
from typing import Any

import psycopg
from psycopg.rows import dict_row

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HACSDatabaseMigration:
    """Asynchronous database migration utility for HACS."""

    def __init__(self, database_url: str):
        self.database_url = database_url

    async def _get_connection(self):
        """Get an asynchronous database connection."""
        return await psycopg.AsyncConnection.connect(
            self.database_url,
            row_factory=dict_row,
            autocommit=True
        )

    async def run_migration(self) -> bool:
        """Run the complete HACS database migration asynchronously."""
        try:
            logger.info("Starting HACS database migration...")

            async with await self._get_connection() as conn:
                async with conn.cursor() as cursor:
                    # Create schemas
                    await self._create_schemas(cursor)

                    # Create core tables
                    await self._create_core_tables(cursor)

                    # Create clinical tables
                    await self._create_clinical_tables(cursor)

                    # Create organizational tables
                    await self._create_organizational_tables(cursor)

                    # Create workflow tables
                    await self._create_workflow_tables(cursor)

                    # Create registry tables
                    await self._create_registry_tables(cursor)

                    # Create agent tables
                    await self._create_agent_tables(cursor)

                    # Create admin tables
                    await self._create_admin_tables(cursor)

                    # Create audit tables
                    await self._create_audit_tables(cursor)

                    # Create indexes
                    await self._create_indexes(cursor)

                    # Create functions and triggers
                    await self._create_functions_and_triggers(cursor)

                    logger.info("HACS database migration completed successfully!")
                    return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False

    async def _create_schemas(self, cursor):
        """Create database schemas asynchronously."""
        # First ensure pgvector extension is enabled
        await cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        logger.info("✓ pgvector extension enabled")

        schemas = [
            "hacs_core",
            "hacs_clinical",
            "hacs_registry",
            "hacs_agents",
            "hacs_admin",
            "hacs_audit"
        ]

        logger.info("Creating database schemas...")
        for schema in schemas:
            await cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
            logger.info(f"✓ Schema {schema} created")

    async def _create_core_tables(self, cursor):
        """Create core HACS tables asynchronously."""
        logger.info("Creating core tables...")

        # Generic resources table
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hacs_core.resources (
                id TEXT PRIMARY KEY,
                resource_type TEXT NOT NULL,
                data JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                created_by TEXT,
                updated_by TEXT
            );
        """)

        # Patients table
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hacs_core.patients (
                id TEXT PRIMARY KEY,
                given TEXT[],
                family TEXT,
                full_name TEXT,
                birth_date DATE,
                gender TEXT,
                active BOOLEAN DEFAULT TRUE,
                deceased BOOLEAN DEFAULT FALSE,
                marital_status TEXT,
                multiple_birth BOOLEAN DEFAULT FALSE,
                photo_url TEXT,
                telecom JSONB,
                address JSONB,
                contact JSONB,
                communication JSONB,
                general_practitioner TEXT[],
                managing_organization TEXT,
                link JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # Observations table
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hacs_core.observations (
                id TEXT PRIMARY KEY,
                identifier JSONB,
                based_on TEXT[],
                part_of TEXT[],
                status TEXT NOT NULL,
                category JSONB,
                code JSONB NOT NULL,
                subject TEXT NOT NULL,
                focus TEXT[],
                encounter TEXT,
                effective_datetime TIMESTAMP WITH TIME ZONE,
                issued TIMESTAMP WITH TIME ZONE,
                performer TEXT[],
                value_quantity JSONB,
                value_codeable_concept JSONB,
                value_string TEXT,
                value_boolean BOOLEAN,
                value_integer INTEGER,
                value_range JSONB,
                value_ratio JSONB,
                value_sampled_data JSONB,
                value_time TIME,
                value_datetime TIMESTAMP WITH TIME ZONE,
                value_period JSONB,
                data_absent_reason JSONB,
                interpretation JSONB,
                note JSONB,
                body_site JSONB,
                method JSONB,
                specimen TEXT,
                device TEXT,
                reference_range JSONB,
                has_member TEXT[],
                derived_from TEXT[],
                component JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # Encounters table
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hacs_core.encounters (
                id TEXT PRIMARY KEY,
                identifier JSONB,
                status TEXT NOT NULL,
                status_history JSONB,
                class JSONB NOT NULL,
                class_history JSONB,
                type JSONB,
                service_type JSONB,
                priority JSONB,
                subject TEXT,
                episode_of_care TEXT[],
                based_on TEXT[],
                participant JSONB,
                appointment TEXT[],
                period JSONB,
                length JSONB,
                reason_code JSONB,
                reason_reference TEXT[],
                diagnosis JSONB,
                account TEXT[],
                hospitalization JSONB,
                location JSONB,
                service_provider TEXT,
                part_of TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        logger.info("✓ Core tables created")

    async def _create_clinical_tables(self, cursor):
        """Create clinical tables asynchronously."""
        logger.info("Creating clinical tables...")

        # Conditions table
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hacs_clinical.conditions (
                id TEXT PRIMARY KEY,
                identifier JSONB,
                clinical_status JSONB NOT NULL,
                verification_status JSONB,
                category JSONB,
                severity JSONB,
                code JSONB,
                body_site JSONB,
                subject TEXT NOT NULL,
                encounter TEXT,
                onset_datetime TIMESTAMP WITH TIME ZONE,
                onset_age JSONB,
                onset_period JSONB,
                onset_range JSONB,
                onset_string TEXT,
                abatement_datetime TIMESTAMP WITH TIME ZONE,
                abatement_age JSONB,
                abatement_period JSONB,
                abatement_range JSONB,
                abatement_string TEXT,
                recorded_date DATE,
                recorder TEXT,
                asserter TEXT,
                stage JSONB,
                evidence JSONB,
                note JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # Medications table
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hacs_clinical.medications (
                id TEXT PRIMARY KEY,
                identifier JSONB,
                code JSONB,
                status TEXT,
                manufacturer TEXT,
                form JSONB,
                amount JSONB,
                ingredient JSONB,
                batch JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # Medication Requests table
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hacs_clinical.medication_requests (
                id TEXT PRIMARY KEY,
                identifier JSONB,
                status TEXT NOT NULL,
                status_reason JSONB,
                intent TEXT NOT NULL,
                category JSONB,
                priority TEXT,
                do_not_perform BOOLEAN DEFAULT FALSE,
                reported_boolean BOOLEAN,
                reported_reference TEXT,
                medication_codeable_concept JSONB,
                medication_reference TEXT,
                subject TEXT NOT NULL,
                encounter TEXT,
                supporting_information TEXT[],
                authored_on TIMESTAMP WITH TIME ZONE,
                requester TEXT,
                performer TEXT,
                performer_type JSONB,
                recorder TEXT,
                reason_code JSONB,
                reason_reference TEXT[],
                instantiates_canonical TEXT[],
                instantiates_uri TEXT[],
                based_on TEXT[],
                group_identifier JSONB,
                course_of_therapy_type JSONB,
                insurance TEXT[],
                note JSONB,
                dosage_instruction JSONB,
                dispense_request JSONB,
                substitution JSONB,
                prior_prescription TEXT,
                detection_issue TEXT[],
                event_history TEXT[],
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # Procedures table
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hacs_clinical.procedures (
                id TEXT PRIMARY KEY,
                identifier JSONB,
                instantiates_canonical TEXT[],
                instantiates_uri TEXT[],
                based_on TEXT[],
                part_of TEXT[],
                status TEXT NOT NULL,
                status_reason JSONB,
                category JSONB,
                code JSONB,
                subject TEXT NOT NULL,
                encounter TEXT,
                performed_datetime TIMESTAMP WITH TIME ZONE,
                performed_period JSONB,
                performed_string TEXT,
                performed_age JSONB,
                performed_range JSONB,
                recorder TEXT,
                asserter TEXT,
                performer JSONB,
                location TEXT,
                reason_code JSONB,
                reason_reference TEXT[],
                body_site JSONB,
                outcome JSONB,
                report TEXT[],
                complication JSONB,
                complication_detail TEXT[],
                follow_up JSONB,
                note JSONB,
                focal_device JSONB,
                used_reference TEXT[],
                used_code JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # Allergy Intolerances table
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hacs_clinical.allergy_intolerances (
                id TEXT PRIMARY KEY,
                identifier JSONB,
                clinical_status JSONB,
                verification_status JSONB,
                type TEXT,
                category TEXT[],
                criticality TEXT,
                code JSONB,
                patient TEXT NOT NULL,
                encounter TEXT,
                onset_datetime TIMESTAMP WITH TIME ZONE,
                onset_age JSONB,
                onset_period JSONB,
                onset_range JSONB,
                onset_string TEXT,
                recorded_date TIMESTAMP WITH TIME ZONE,
                recorder TEXT,
                asserter TEXT,
                last_occurrence TIMESTAMP WITH TIME ZONE,
                note JSONB,
                reaction JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # Goals table
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hacs_clinical.goals (
                id TEXT PRIMARY KEY,
                identifier JSONB,
                lifecycle_status TEXT NOT NULL,
                achievement_status JSONB,
                category JSONB,
                continuous BOOLEAN DEFAULT FALSE,
                priority JSONB,
                description JSONB NOT NULL,
                subject TEXT NOT NULL,
                start_date DATE,
                start_codeable_concept JSONB,
                target JSONB,
                status_date DATE,
                status_reason TEXT,
                expressed_by TEXT,
                addresses TEXT[],
                note JSONB,
                outcome_code JSONB,
                outcome_reference TEXT[],
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # Service Requests table
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hacs_clinical.service_requests (
                id TEXT PRIMARY KEY,
                identifier JSONB,
                instantiates_canonical TEXT[],
                instantiates_uri TEXT[],
                based_on TEXT[],
                replaces TEXT[],
                requisition JSONB,
                status TEXT NOT NULL,
                intent TEXT NOT NULL,
                category JSONB,
                priority TEXT,
                do_not_perform BOOLEAN DEFAULT FALSE,
                code JSONB,
                order_detail JSONB,
                quantity_quantity JSONB,
                quantity_ratio JSONB,
                quantity_range JSONB,
                subject TEXT NOT NULL,
                encounter TEXT,
                occurrence_datetime TIMESTAMP WITH TIME ZONE,
                occurrence_period JSONB,
                occurrence_timing JSONB,
                as_needed_boolean BOOLEAN,
                as_needed_codeable_concept JSONB,
                authored_on TIMESTAMP WITH TIME ZONE,
                requester TEXT,
                performer_type JSONB,
                performer TEXT[],
                location_code JSONB,
                location_reference TEXT[],
                reason_code JSONB,
                reason_reference TEXT[],
                insurance TEXT[],
                supporting_info TEXT[],
                specimen TEXT[],
                body_site JSONB,
                note JSONB,
                patient_instruction TEXT,
                relevant_history TEXT[],
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # Family Member History table
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hacs_clinical.family_member_history (
                id TEXT PRIMARY KEY,
                identifier JSONB,
                instantiates_canonical TEXT[],
                instantiates_uri TEXT[],
                status TEXT NOT NULL,
                data_absent_reason JSONB,
                patient TEXT NOT NULL,
                date TIMESTAMP WITH TIME ZONE,
                name TEXT,
                relationship JSONB NOT NULL,
                sex JSONB,
                born_period JSONB,
                born_date DATE,
                born_string TEXT,
                age_age JSONB,
                age_range JSONB,
                age_string TEXT,
                estimated_age BOOLEAN,
                deceased_boolean BOOLEAN,
                deceased_age JSONB,
                deceased_range JSONB,
                deceased_date DATE,
                deceased_string TEXT,
                reason_code JSONB,
                reason_reference TEXT[],
                note JSONB,
                condition JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # Risk Assessments table
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hacs_clinical.risk_assessments (
                id TEXT PRIMARY KEY,
                identifier JSONB,
                based_on TEXT,
                parent TEXT,
                status TEXT NOT NULL,
                method JSONB,
                code JSONB,
                subject TEXT NOT NULL,
                encounter TEXT,
                occurrence_datetime TIMESTAMP WITH TIME ZONE,
                occurrence_period JSONB,
                condition TEXT,
                performer TEXT,
                reason_code JSONB,
                reason_reference TEXT[],
                basis TEXT[],
                prediction JSONB,
                mitigation TEXT,
                note JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        logger.info("✓ Clinical tables created")

    async def _create_organizational_tables(self, cursor):
        """Create organizational tables asynchronously."""
        logger.info("Creating organizational tables...")

        # Organizations table
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hacs_core.organizations (
                id TEXT PRIMARY KEY,
                identifier JSONB,
                active BOOLEAN DEFAULT TRUE,
                type JSONB,
                name TEXT NOT NULL,
                alias TEXT[],
                description TEXT,
                contact JSONB,
                part_of TEXT,
                endpoint TEXT[],
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # Organization Contacts table
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hacs_core.organization_contacts (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL REFERENCES hacs_core.organizations(id),
                purpose JSONB,
                name_family TEXT,
                name_given TEXT[],
                name_prefix TEXT[],
                name_suffix TEXT[],
                name_period JSONB,
                telecom JSONB,
                address JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # Organization Qualifications table
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hacs_core.organization_qualifications (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL REFERENCES hacs_core.organizations(id),
                identifier JSONB,
                code JSONB NOT NULL,
                period JSONB,
                issuer TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        logger.info("✓ Organizational tables created")

    async def _create_workflow_tables(self, cursor):
        """Create workflow and clinical reasoning tables asynchronously."""
        logger.info("Creating workflow tables...")

        # Plan Definitions table
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hacs_clinical.plan_definitions (
                id TEXT PRIMARY KEY,
                url TEXT,
                identifier JSONB,
                version TEXT,
                name TEXT,
                title TEXT,
                subtitle TEXT,
                type JSONB,
                status TEXT NOT NULL,
                experimental BOOLEAN DEFAULT FALSE,
                subject_codeable_concept JSONB,
                subject_reference TEXT,
                date TIMESTAMP WITH TIME ZONE,
                publisher TEXT,
                contact JSONB,
                description TEXT,
                use_context JSONB,
                jurisdiction JSONB,
                purpose TEXT,
                usage TEXT,
                copyright TEXT,
                approval_date DATE,
                last_review_date DATE,
                effective_period JSONB,
                topic JSONB,
                author JSONB,
                editor JSONB,
                reviewer JSONB,
                endorser JSONB,
                related_artifact JSONB,
                library TEXT[],
                goal JSONB,
                action JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # Activity Definitions table
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hacs_clinical.activity_definitions (
                id TEXT PRIMARY KEY,
                url TEXT,
                identifier JSONB,
                version TEXT,
                name TEXT,
                title TEXT,
                subtitle TEXT,
                status TEXT NOT NULL,
                experimental BOOLEAN DEFAULT FALSE,
                subject_codeable_concept JSONB,
                subject_reference TEXT,
                date TIMESTAMP WITH TIME ZONE,
                publisher TEXT,
                contact JSONB,
                description TEXT,
                use_context JSONB,
                jurisdiction JSONB,
                purpose TEXT,
                usage TEXT,
                copyright TEXT,
                approval_date DATE,
                last_review_date DATE,
                effective_period JSONB,
                topic JSONB,
                author JSONB,
                editor JSONB,
                reviewer JSONB,
                endorser JSONB,
                related_artifact JSONB,
                library TEXT[],
                kind TEXT,
                profile TEXT,
                code JSONB,
                intent TEXT,
                priority TEXT,
                do_not_perform BOOLEAN DEFAULT FALSE,
                timing_timing JSONB,
                timing_datetime TIMESTAMP WITH TIME ZONE,
                timing_age JSONB,
                timing_period JSONB,
                timing_range JSONB,
                timing_duration JSONB,
                location TEXT,
                participant JSONB,
                product_reference TEXT,
                product_codeable_concept JSONB,
                quantity JSONB,
                dosage JSONB,
                body_site JSONB,
                specimen_requirement TEXT[],
                observation_requirement TEXT[],
                observation_result_requirement TEXT[],
                transform TEXT,
                dynamic_value JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # Libraries table
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hacs_clinical.libraries (
                id TEXT PRIMARY KEY,
                url TEXT,
                identifier JSONB,
                version TEXT,
                name TEXT,
                title TEXT,
                subtitle TEXT,
                status TEXT NOT NULL,
                experimental BOOLEAN DEFAULT FALSE,
                type JSONB NOT NULL,
                subject_codeable_concept JSONB,
                subject_reference TEXT,
                date TIMESTAMP WITH TIME ZONE,
                publisher TEXT,
                contact JSONB,
                description TEXT,
                use_context JSONB,
                jurisdiction JSONB,
                purpose TEXT,
                usage TEXT,
                copyright TEXT,
                approval_date DATE,
                last_review_date DATE,
                effective_period JSONB,
                topic JSONB,
                author JSONB,
                editor JSONB,
                reviewer JSONB,
                endorser JSONB,
                related_artifact JSONB,
                parameter JSONB,
                data_requirement JSONB,
                content JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # Evidence Variables table
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hacs_clinical.evidence_variables (
                id TEXT PRIMARY KEY,
                url TEXT,
                identifier JSONB,
                version TEXT,
                name TEXT,
                title TEXT,
                short_title TEXT,
                subtitle TEXT,
                status TEXT NOT NULL,
                date TIMESTAMP WITH TIME ZONE,
                publisher TEXT,
                contact JSONB,
                description TEXT,
                note JSONB,
                use_context JSONB,
                jurisdiction JSONB,
                copyright TEXT,
                approval_date DATE,
                last_review_date DATE,
                effective_period JSONB,
                topic JSONB,
                author JSONB,
                editor JSONB,
                reviewer JSONB,
                endorser JSONB,
                related_artifact JSONB,
                actual_definition TEXT,
                characteristic JSONB NOT NULL,
                handling TEXT,
                category JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        logger.info("✓ Workflow tables created")

    async def _create_registry_tables(self, cursor):
        """Create registry and metadata tables asynchronously."""
        logger.info("Creating registry tables...")

        # Model Versions table
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hacs_registry.model_versions (
                id TEXT PRIMARY KEY,
                model_name TEXT NOT NULL,
                version TEXT NOT NULL,
                description TEXT,
                schema_definition JSONB NOT NULL,
                tags TEXT[],
                status TEXT DEFAULT 'published',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                UNIQUE(model_name, version)
            );
        """)

        # Knowledge Items table with pgvector support
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hacs_registry.knowledge_items (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                knowledge_type TEXT DEFAULT 'fact',
                tags TEXT[],
                metadata JSONB,
                source TEXT,
                content_hash TEXT,
                full_resource JSONB,
                embedding vector(1536),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        logger.info("✓ Registry tables created")

    async def _create_agent_tables(self, cursor):
        """Create agent and memory tables asynchronously."""
        logger.info("Creating agent tables...")

        # Agent Messages table
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hacs_agents.agent_messages (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tool_calls JSONB,
                metadata JSONB,
                session_id TEXT,
                parent_message_id TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # Memory Blocks table
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hacs_agents.memory_blocks (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                summary TEXT,
                metadata JSONB,
                related_memories TEXT[],
                importance_score FLOAT DEFAULT 0.5,
                confidence_score FLOAT DEFAULT 0.8,
                tags TEXT[],
                access_count INTEGER DEFAULT 0,
                vector_id TEXT,
                last_accessed TIMESTAMP WITH TIME ZONE,
                last_summarized TIMESTAMP WITH TIME ZONE,
                session_id TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # Actor Sessions table
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hacs_agents.actor_sessions (
                id TEXT PRIMARY KEY,
                actor_id TEXT NOT NULL,
                session_status TEXT DEFAULT 'inactive',
                last_activity TIMESTAMP WITH TIME ZONE,
                metadata JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        logger.info("✓ Agent tables created")

    async def _create_admin_tables(self, cursor):
        """Create admin and configuration tables asynchronously."""
        logger.info("Creating admin tables...")

        # System Configuration table
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hacs_admin.system_configuration (
                id TEXT PRIMARY KEY,
                config_key TEXT UNIQUE NOT NULL,
                config_value JSONB NOT NULL,
                description TEXT,
                is_sensitive BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        logger.info("✓ Admin tables created")

    async def _create_audit_tables(self, cursor):
        """Create audit and logging tables asynchronously."""
        logger.info("Creating audit tables...")

        # System Audit Log table
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS hacs_audit.system_audit_log (
                id TEXT PRIMARY KEY,
                actor_id TEXT,
                action TEXT NOT NULL,
                resource_type TEXT,
                resource_id TEXT,
                details JSONB,
                ip_address INET,
                user_agent TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        logger.info("✓ Audit tables created")

    async def _create_indexes(self, cursor):
        """Create database indexes asynchronously."""
        logger.info("Creating indexes...")

        # Core table indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_patients_family ON hacs_core.patients(family);",
            "CREATE INDEX IF NOT EXISTS idx_patients_birth_date ON hacs_core.patients(birth_date);",
            "CREATE INDEX IF NOT EXISTS idx_patients_active ON hacs_core.patients(active);",
            "CREATE INDEX IF NOT EXISTS idx_observations_subject ON hacs_core.observations(subject);",
            "CREATE INDEX IF NOT EXISTS idx_observations_code ON hacs_core.observations USING GIN(code);",
            "CREATE INDEX IF NOT EXISTS idx_observations_effective_datetime ON hacs_core.observations(effective_datetime);",
            "CREATE INDEX IF NOT EXISTS idx_encounters_subject ON hacs_core.encounters(subject);",
            "CREATE INDEX IF NOT EXISTS idx_encounters_period ON hacs_core.encounters USING GIN(period);",
            "CREATE INDEX IF NOT EXISTS idx_conditions_subject ON hacs_clinical.conditions(subject);",
            "CREATE INDEX IF NOT EXISTS idx_conditions_code ON hacs_clinical.conditions USING GIN(code);",
            "CREATE INDEX IF NOT EXISTS idx_medication_requests_subject ON hacs_clinical.medication_requests(subject);",
            "CREATE INDEX IF NOT EXISTS idx_procedures_subject ON hacs_clinical.procedures(subject);",
            "CREATE INDEX IF NOT EXISTS idx_allergy_intolerances_patient ON hacs_clinical.allergy_intolerances(patient);",
            "CREATE INDEX IF NOT EXISTS idx_goals_subject ON hacs_clinical.goals(subject);",
            "CREATE INDEX IF NOT EXISTS idx_service_requests_subject ON hacs_clinical.service_requests(subject);",
            "CREATE INDEX IF NOT EXISTS idx_family_member_history_patient ON hacs_clinical.family_member_history(patient);",
            "CREATE INDEX IF NOT EXISTS idx_risk_assessments_subject ON hacs_clinical.risk_assessments(subject);",
            "CREATE INDEX IF NOT EXISTS idx_organizations_name ON hacs_core.organizations(name);",
            "CREATE INDEX IF NOT EXISTS idx_organization_contacts_org_id ON hacs_core.organization_contacts(organization_id);",
            "CREATE INDEX IF NOT EXISTS idx_organization_qualifications_org_id ON hacs_core.organization_qualifications(organization_id);",
            "CREATE INDEX IF NOT EXISTS idx_knowledge_items_embedding ON hacs_registry.knowledge_items USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);",
            "CREATE INDEX IF NOT EXISTS idx_knowledge_items_tags ON hacs_registry.knowledge_items USING GIN(tags);",
            "CREATE INDEX IF NOT EXISTS idx_agent_messages_session_id ON hacs_agents.agent_messages(session_id);",
            "CREATE INDEX IF NOT EXISTS idx_memory_blocks_agent_id ON hacs_agents.memory_blocks(agent_id);",
            "CREATE INDEX IF NOT EXISTS idx_memory_blocks_session_id ON hacs_agents.memory_blocks(session_id);",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_actor_id ON hacs_audit.system_audit_log(actor_id);",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON hacs_audit.system_audit_log(created_at);",
        ]

        for index_sql in indexes:
            await cursor.execute(index_sql)

        logger.info("✓ Indexes created")

    async def _create_functions_and_triggers(self, cursor):
        """Create database functions and triggers asynchronously."""
        logger.info("Creating functions and triggers...")

        # Updated timestamp trigger function
        await cursor.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """)

        # Triggers for updated_at
        tables_with_updated_at = [
            "hacs_core.resources",
            "hacs_core.patients",
            "hacs_core.observations",
            "hacs_core.encounters",
            "hacs_core.organizations",
            "hacs_core.organization_contacts",
            "hacs_core.organization_qualifications",
            "hacs_clinical.conditions",
            "hacs_clinical.medications",
            "hacs_clinical.medication_requests",
            "hacs_clinical.procedures",
            "hacs_clinical.allergy_intolerances",
            "hacs_clinical.goals",
            "hacs_clinical.service_requests",
            "hacs_clinical.family_member_history",
            "hacs_clinical.risk_assessments",
            "hacs_clinical.plan_definitions",
            "hacs_clinical.activity_definitions",
            "hacs_clinical.libraries",
            "hacs_clinical.evidence_variables",
            "hacs_registry.model_versions",
            "hacs_registry.knowledge_items",
            "hacs_agents.agent_messages",
            "hacs_agents.memory_blocks",
            "hacs_agents.actor_sessions",
            "hacs_admin.system_configuration",
        ]

        for table in tables_with_updated_at:
            trigger_name = f"update_{table.replace('.', '_').replace('hacs_', '')}_updated_at"
            await cursor.execute(f"""
                CREATE TRIGGER {trigger_name}
                    BEFORE UPDATE ON {table}
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column();
            """)

        logger.info("✓ Functions and triggers created")


async def run_migration(database_url: str = None) -> bool:
    """Run HACS database migration asynchronously."""
    if not database_url:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            logger.error("DATABASE_URL not provided and not found in environment")
            return False

    migration = HACSDatabaseMigration(database_url)
    return await migration.run_migration()


async def get_migration_status(database_url: str = None) -> dict[str, Any]:
    """Get migration status asynchronously."""
    if not database_url:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            return {"error": "DATABASE_URL not provided"}

    try:
        async with await psycopg.AsyncConnection.connect(database_url, row_factory=dict_row) as conn:
            async with conn.cursor() as cursor:
                # Count tables across all HACS schemas
                await cursor.execute("""
                    SELECT schemaname, COUNT(*) as table_count
                    FROM pg_tables
                    WHERE schemaname LIKE 'hacs_%'
                    GROUP BY schemaname
                    ORDER BY schemaname;
                """)

                schema_tables = await cursor.fetchall()

                # Expected total tables
                expected_tables = 23  # Updated count including Organization tables

                total_tables = sum(row["table_count"] for row in schema_tables)

                # Check if pgvector extension exists
                await cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector');")
                pgvector_enabled = (await cursor.fetchone())["exists"]

                return {
                    "migration_complete": total_tables >= expected_tables,
                    "total_tables": total_tables,
                    "expected_tables": expected_tables,
                    "pgvector_enabled": pgvector_enabled,
                    "schema_breakdown": {row["schemaname"]: row["table_count"] for row in schema_tables},
                    "schemas_created": len(schema_tables)
                }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Command line execution
    import sys
    database_url = sys.argv[1] if len(sys.argv) > 1 else None
    success = asyncio.run(run_migration(database_url))
    sys.exit(0 if success else 1)
