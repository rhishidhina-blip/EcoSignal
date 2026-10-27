CREATE TABLE `eco_assets` (
	`owner` text NOT NULL,
	`id` text NOT NULL,
	`sample` text NOT NULL,
	`kind` text NOT NULL,
	`checksum` text NOT NULL,
	`mime` text NOT NULL,
	`bytes` integer NOT NULL,
	`object_key` text NOT NULL,
	`source` text,
	`width` integer,
	`height` integer,
	`created` text NOT NULL,
	PRIMARY KEY(`owner`, `id`)
);
--> statement-breakpoint
CREATE UNIQUE INDEX `eco_asset_deduplicate` ON `eco_assets` (`owner`,`sample`,`kind`,`checksum`);--> statement-breakpoint
CREATE INDEX `eco_asset_sample` ON `eco_assets` (`owner`,`sample`);--> statement-breakpoint
CREATE TABLE `eco_audit` (
	`owner` text NOT NULL,
	`id` text NOT NULL,
	`previous` text NOT NULL,
	`hash` text NOT NULL,
	`canonical` text NOT NULL,
	`created` text NOT NULL,
	PRIMARY KEY(`owner`, `id`)
);
--> statement-breakpoint
CREATE UNIQUE INDEX `eco_audit_no_forks` ON `eco_audit` (`owner`,`previous`);--> statement-breakpoint
CREATE UNIQUE INDEX `eco_audit_hash` ON `eco_audit` (`owner`,`hash`);--> statement-breakpoint
CREATE TABLE `eco_dataset_items` (
	`owner` text NOT NULL,
	`dataset` text NOT NULL,
	`id` text NOT NULL,
	`sample` text NOT NULL,
	`site_group` text NOT NULL,
	`split` text NOT NULL,
	`staging` text NOT NULL,
	`payload` text NOT NULL,
	PRIMARY KEY(`owner`, `dataset`, `id`)
);
--> statement-breakpoint
CREATE UNIQUE INDEX `eco_dataset_sample` ON `eco_dataset_items` (`owner`,`dataset`,`sample`);--> statement-breakpoint
CREATE TABLE `eco_entities` (
	`owner` text NOT NULL,
	`kind` text NOT NULL,
	`id` text NOT NULL,
	`version` integer DEFAULT 1 NOT NULL,
	`payload` text NOT NULL,
	`created` text NOT NULL,
	`updated` text NOT NULL,
	PRIMARY KEY(`owner`, `kind`, `id`)
);
--> statement-breakpoint
CREATE INDEX `eco_kind_updated` ON `eco_entities` (`owner`,`kind`,`updated`);--> statement-breakpoint
CREATE TABLE `eco_site_splits` (
	`owner` text NOT NULL,
	`site_group` text NOT NULL,
	`split` text NOT NULL,
	PRIMARY KEY(`owner`, `site_group`)
);
