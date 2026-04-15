import com.android.build.gradle.BaseExtension

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

// Firebase and other plugins may pin compileSdk 34; Platform 34 downloads can fail (EOF).
// Force compileSdk to match the app module and an installed platform (e.g. 36).
subprojects {
    afterEvaluate {
        extensions.findByType(BaseExtension::class.java)?.compileSdkVersion(36)
    }
}

val newBuildDir: Directory =
    rootProject.layout.buildDirectory
        .dir("../../build")
        .get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}
subprojects {
    project.evaluationDependsOn(":app")
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
