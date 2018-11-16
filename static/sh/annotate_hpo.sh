cd /opt/services/case/local/ccp-nlp-pipelines;
mvn -f ./nlp-pipelines-conceptmapper/pom.xml exec:java -Dexec.mainClass='edu.ucdenver.ccp.nlp.pipelines.conceptmapper.EntityFinder' -Dexec.args='/opt/services/case/tmp/annotate/hpo/input /opt/services/case/tmp/annotate/hpo/output CHEBI /opt/services/case/data/PubCases/ontologies/HP/hp_20181009.obo ./DictDir/HP_20181009 false';
